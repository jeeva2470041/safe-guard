"""
Session Service — Manages Antigravity session bindings and goal associations in MongoDB.

Provides:
- start_or_update_antigravity_session: Automatically creates or updates a dynamic Goal Policy from user prompts.
- resolve_active_goal_for_session: Accurately looks up the active goal by conversationId.
- get_antigravity_connection_status: Real-time telemetry for frontend auto-sync.
"""

import uuid
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

from app.database.connection import get_database
from app.services.goal_analyzer import GoalAnalyzerService

logger = logging.getLogger("agent_guard.session_service")


async def start_or_update_antigravity_session(
    conversation_id: str,
    user_prompt: str,
    workspace_paths: Optional[List[str]] = None,
    invocation_num: int = 1,
    agent: str = "antigravity"
) -> Dict[str, Any]:
    """
    Called by PreInvocation hook when user enters a prompt in Antigravity.
    Automatically generates or updates a Goal Policy, maps conversationId -> goalId -> goalVersion.
    """
    db = get_database()
    now_iso = datetime.now(timezone.utc).isoformat()
    workspace_paths = workspace_paths or []
    cleaned_prompt = user_prompt.strip()

    # Look up existing session for this conversationId
    existing_session = await db.agent_sessions.find_one({
        "$or": [{"conversationId": conversation_id}, {"sessionId": conversation_id}]
    })

    analyzer = GoalAnalyzerService()

    if not existing_session:
        # ── Step 1: New Conversation -> Create New Goal & Dynamic Policy ──
        goal_id = f"G-{uuid.uuid4().hex[:6].upper()}"
        goal_policy = await analyzer.analyze_goal(cleaned_prompt)

        initial_version = {
            "version": 1,
            "userGoal": cleaned_prompt,
            "constraints": goal_policy.get("constraints", []),
            "goalPolicy": goal_policy,
            "createdAt": now_iso,
            "changeReason": "Initial prompt from Antigravity conversation",
            "status": "ACTIVE"
        }

        goal_doc = {
            "goalId": goal_id,
            "conversationId": conversation_id,
            "userGoal": cleaned_prompt,
            "constraints": goal_policy.get("constraints", []),
            "goalPolicy": goal_policy,
            "goalVersion": 1,
            "versionHistory": [initial_version],
            "status": "ACTIVE",
            "agent": agent,
            "workspacePaths": workspace_paths,
            "createdAt": now_iso,
            "updatedAt": now_iso,
        }

        await db.goals.insert_one(goal_doc)

        session_doc = {
            "conversationId": conversation_id,
            "sessionId": conversation_id,
            "goalId": goal_id,
            "goalVersion": 1,
            "agent": agent,
            "status": "ACTIVE",
            "userGoal": cleaned_prompt,
            "lastPrompt": cleaned_prompt,
            "workspacePaths": workspace_paths,
            "createdAt": now_iso,
            "lastSeenAt": now_iso,
            "interceptedCount": 0,
        }

        await db.agent_sessions.update_one(
            {"conversationId": conversation_id},
            {"$set": session_doc},
            upsert=True
        )

        logger.info(f"[SESSION START] Created new goal {goal_id} (v1) for conversation {conversation_id}")

        return {
            "conversationId": conversation_id,
            "sessionId": conversation_id,
            "goalId": goal_id,
            "goalVersion": 1,
            "userGoal": cleaned_prompt,
            "goalPolicy": goal_policy,
            "status": "ACTIVE",
            "isNewGoal": True,
            "isVersionUpdate": False
        }

    else:
        # ── Step 2: Existing Session -> Check if prompt changed / expanded ──
        goal_id = existing_session.get("goalId")
        existing_goal = await db.goals.find_one({"goalId": goal_id})
        last_prompt = existing_session.get("lastPrompt", "")

        # If prompt is identical or empty, simply touch lastSeenAt and reactivate session
        if not cleaned_prompt or cleaned_prompt == last_prompt:
            await db.agent_sessions.update_one(
                {"conversationId": conversation_id},
                {"$set": {"lastSeenAt": now_iso, "workspacePaths": workspace_paths, "status": "ACTIVE"}}
            )
            policy = existing_goal.get("goalPolicy") if existing_goal else {}
            current_ver = existing_goal.get("goalVersion", 1) if existing_goal else 1
            return {
                "conversationId": conversation_id,
                "sessionId": conversation_id,
                "goalId": goal_id,
                "goalVersion": current_ver,
                "userGoal": existing_goal.get("userGoal", cleaned_prompt) if existing_goal else cleaned_prompt,
                "goalPolicy": policy,
                "status": existing_goal.get("status", "ACTIVE") if existing_goal else "ACTIVE",
                "isNewGoal": False,
                "isVersionUpdate": False
            }

        # User modified/extended the prompt in the same conversation -> create new goalVersion
        current_version = existing_goal.get("goalVersion", 1) if existing_goal else 1
        new_version_num = current_version + 1

        # Synthesize updated dynamic policy
        new_policy = await analyzer.analyze_goal(cleaned_prompt)

        new_version_entry = {
            "version": new_version_num,
            "userGoal": cleaned_prompt,
            "constraints": new_policy.get("constraints", []),
            "goalPolicy": new_policy,
            "createdAt": now_iso,
            "changeReason": f"Antigravity prompt updated in turn {invocation_num}",
            "status": "ACTIVE"
        }

        if not existing_goal:
            # Recreate missing goal document in DB
            new_policy = await analyzer.analyze_goal(cleaned_prompt)
            initial_version = {
                "version": 1,
                "userGoal": cleaned_prompt,
                "constraints": new_policy.get("constraints", []),
                "goalPolicy": new_policy,
                "createdAt": now_iso,
                "changeReason": f"Antigravity prompt updated in turn {invocation_num}",
                "status": "ACTIVE"
            }
            goal_doc = {
                "goalId": goal_id,
                "conversationId": conversation_id,
                "userGoal": cleaned_prompt,
                "constraints": new_policy.get("constraints", []),
                "goalPolicy": new_policy,
                "goalVersion": 1,
                "versionHistory": [initial_version],
                "status": "ACTIVE",
                "agent": agent,
                "workspacePaths": workspace_paths,
                "createdAt": now_iso,
                "updatedAt": now_iso,
            }
            await db.goals.update_one({"goalId": goal_id}, {"$set": goal_doc}, upsert=True)
        else:
            await db.goals.update_one(
                {"goalId": goal_id},
                {
                    "$set": {
                        "userGoal": cleaned_prompt,
                        "constraints": new_policy.get("constraints", []),
                        "goalPolicy": new_policy,
                        "goalVersion": new_version_num,
                        "status": "ACTIVE",
                        "pauseReason": None,
                        "recentDivergentAction": None,
                        "updatedAt": now_iso
                    },
                    "$push": {
                        "versionHistory": new_version_entry
                    }
                },
                upsert=True
            )

        await db.agent_sessions.update_one(
            {"conversationId": conversation_id},
            {
                "$set": {
                    "goalVersion": new_version_num,
                    "userGoal": cleaned_prompt,
                    "lastPrompt": cleaned_prompt,
                    "lastSeenAt": now_iso,
                    "workspacePaths": workspace_paths,
                    "status": "ACTIVE"
                }
            }
        )

        logger.info(f"[SESSION UPDATE] Updated goal {goal_id} to v{new_version_num} for conversation {conversation_id}")

        return {
            "conversationId": conversation_id,
            "sessionId": conversation_id,
            "goalId": goal_id,
            "goalVersion": new_version_num,
            "userGoal": cleaned_prompt,
            "goalPolicy": new_policy,
            "status": "ACTIVE",
            "isNewGoal": False,
            "isVersionUpdate": True
        }


async def bind_session(conversation_id: str, goal_id: str, agent: str = "antigravity") -> Dict[str, Any]:
    """Manually bind an Antigravity conversation or session to an Agent Guard goal."""
    db = get_database()
    now_iso = datetime.now(timezone.utc).isoformat()

    goal = await db.goals.find_one({"goalId": goal_id})
    goal_ver = goal.get("goalVersion", 1) if goal else 1

    session_doc = {
        "sessionId": conversation_id,
        "conversationId": conversation_id,
        "goalId": goal_id,
        "goalVersion": goal_ver,
        "agent": agent,
        "status": "ACTIVE",
        "createdAt": now_iso,
        "lastSeenAt": now_iso,
        "interceptedCount": 0
    }

    await db.agent_sessions.update_one(
        {"conversationId": conversation_id},
        {"$set": session_doc},
        upsert=True
    )
    return session_doc


async def resolve_active_goal_for_session(
    conversation_id: Optional[str] = None,
    session_id: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Resolve which Agent Guard goal belongs to this incoming Antigravity tool call.
    1. Check explicit session mapping in `agent_sessions` by conversationId or sessionId.
    2. Check direct mapping on `goals` by conversationId.
    3. Fallback to the latest ACTIVE or RUNNING goal in MongoDB.
    """
    db = get_database()
    lookup_id = conversation_id or session_id
    now_iso = datetime.now(timezone.utc).isoformat()

    # 1. Primary resolution: Explicit conversationId -> sessionId mapping in `agent_sessions`
    if lookup_id:
        session = await db.agent_sessions.find_one({
            "$or": [{"conversationId": lookup_id}, {"sessionId": lookup_id}]
        })
        if session and session.get("goalId"):
            goal = await db.goals.find_one({"goalId": session["goalId"]})
            if goal:
                await db.agent_sessions.update_one(
                    {"_id": session["_id"]},
                    {"$set": {"lastSeenAt": now_iso, "status": "ACTIVE"}, "$inc": {"interceptedCount": 1}}
                )
                return goal

    # 2. Check if any goal directly recorded this conversationId
    if lookup_id:
        goal = await db.goals.find_one({"conversationId": lookup_id})
        if goal:
            await db.agent_sessions.update_one(
                {"conversationId": lookup_id},
                {
                    "$set": {
                        "sessionId": lookup_id,
                        "conversationId": lookup_id,
                        "goalId": goal["goalId"],
                        "goalVersion": goal.get("goalVersion", 1),
                        "agent": "antigravity",
                        "status": "ACTIVE",
                        "lastSeenAt": now_iso,
                    },
                    "$setOnInsert": {"createdAt": now_iso},
                    "$inc": {"interceptedCount": 1}
                },
                upsert=True
            )
            return goal

    # 3. Fallback: Lookup the most recently updated active goal
    latest_active_goal = await db.goals.find_one(
        {"status": {"$in": ["ACTIVE", "RUNNING", "WAITING_FOR_APPROVAL", "PAUSED"]}},
        sort=[("createdAt", -1)]
    )

    if latest_active_goal and lookup_id:
        await db.agent_sessions.update_one(
            {"conversationId": lookup_id},
            {
                "$set": {
                    "sessionId": lookup_id,
                    "conversationId": lookup_id,
                    "goalId": latest_active_goal["goalId"],
                    "goalVersion": latest_active_goal.get("goalVersion", 1),
                    "agent": "antigravity",
                    "status": "ACTIVE",
                    "lastSeenAt": now_iso,
                },
                "$setOnInsert": {"createdAt": now_iso},
                "$inc": {"interceptedCount": 1}
            },
            upsert=True
        )
        return latest_active_goal

    return latest_active_goal


async def connect_antigravity_session(session_id: Optional[str] = None, conversation_id: Optional[str] = None) -> Dict[str, Any]:
    """Reactivate the most recent Antigravity session or a specific session."""
    db = get_database()
    now_iso = datetime.now(timezone.utc).isoformat()

    query: Dict[str, Any] = {"agent": "antigravity"}
    if session_id or conversation_id:
        target_id = session_id or conversation_id
        query["$or"] = [{"sessionId": target_id}, {"conversationId": target_id}]

    # Find the most recently seen session matching query
    session = await db.agent_sessions.find_one(query, sort=[("lastSeenAt", -1)])
    if not session:
        # Fallback to any recent session
        session = await db.agent_sessions.find_one({"agent": "antigravity"}, sort=[("createdAt", -1)])

    if session:
        await db.agent_sessions.update_one(
            {"_id": session["_id"]},
            {"$set": {"status": "ACTIVE", "lastSeenAt": now_iso}}
        )
        logger.info(f"[SESSION CONNECT] Reconnected Antigravity session {session.get('sessionId')}")

    return await get_antigravity_connection_status()


async def disconnect_antigravity_session(session_id: Optional[str] = None, conversation_id: Optional[str] = None) -> Dict[str, Any]:
    """Terminate the active Antigravity session/connection without deleting historical logs."""
    db = get_database()
    now_iso = datetime.now(timezone.utc).isoformat()
    
    # When disconnecting the IDE connection, mark all active sessions as DISCONNECTED
    result = await db.agent_sessions.update_many(
        {"status": "ACTIVE"},
        {"$set": {"status": "DISCONNECTED", "disconnectedAt": now_iso}}
    )
    
    logger.info(f"[SESSION DISCONNECT] Disconnected {result.modified_count} active Antigravity sessions")
    return await get_antigravity_connection_status()



async def get_antigravity_connection_status() -> Dict[str, Any]:
    """Retrieve real-time Antigravity connection status based on actual events received."""
    db = get_database()

    # Find the most recent active session with status ACTIVE
    latest_session = await db.agent_sessions.find_one(
        {"agent": "antigravity", "status": "ACTIVE"},
        sort=[("lastSeenAt", -1)]
    )

    # Count total intercepted actions across all antigravity events
    total_intercepted = await db.actions.count_documents({
        "agentId": {"$in": ["antigravity", "GOOGLE-ANTIGRAVITY"]}
    })

    if not latest_session:
        return {
            "connected": False,
            "agent": "antigravity",
            "status": "NOT_CONNECTED",
            "lastSeenAt": None,
            "activeSessionId": None,
            "activeConversationId": None,
            "activeGoalId": None,
            "goalVersion": 1,
            "userGoal": None,
            "workspace": None,
            "lastAction": None,
            "interceptedCount": total_intercepted,
            "allowedCount": 0,
            "blockedCount": 0,
            "approvalCount": 0
        }

    # Fetch associated goal info
    goal_info = None
    goal_id = latest_session.get("goalId")
    if goal_id:
        goal_info = await db.goals.find_one({"goalId": goal_id}, {"_id": 0})

    # Fetch latest action for this session/agent
    last_action_doc = await db.actions.find_one(
        {"agentId": {"$in": ["antigravity", "GOOGLE-ANTIGRAVITY"]}},
        sort=[("timestamp", -1)],
        projection={"_id": 0, "actionId": 1, "actionType": 1, "target": 1, "decision": 1, "timestamp": 1, "description": 1}
    )

    # Aggregate action decision counts for active goal or agent
    query_actions = {"goalId": goal_id} if goal_id else {"agentId": {"$in": ["antigravity", "GOOGLE-ANTIGRAVITY"]}}
    allowed_count = await db.actions.count_documents({**query_actions, "decision": {"$in": ["ALLOW", "APPROVED", "allow"]}})
    blocked_count = await db.actions.count_documents({**query_actions, "decision": {"$in": ["DENY", "BLOCK", "deny"]}})
    approval_count = await db.actions.count_documents({**query_actions, "decision": {"$in": ["REQUIRE_APPROVAL", "ASK", "ask"]}})

    # Extract workspace path if available
    workspace_paths = latest_session.get("workspacePaths", [])
    workspace = workspace_paths[0] if workspace_paths and len(workspace_paths) > 0 else (
        goal_info.get("workspacePaths", [None])[0] if goal_info and goal_info.get("workspacePaths") else None
    )

    return {
        "connected": True,
        "agent": "antigravity",
        "status": "CONNECTED",
        "lastSeenAt": latest_session.get("lastSeenAt"),
        "activeSessionId": latest_session.get("sessionId"),
        "activeConversationId": latest_session.get("conversationId"),
        "activeGoalId": goal_id,
        "goalVersion": latest_session.get("goalVersion", 1),
        "userGoal": latest_session.get("userGoal") or (goal_info.get("userGoal") if goal_info else None),
        "goalPolicy": goal_info.get("goalPolicy") if goal_info else None,
        "workspace": workspace,
        "lastAction": last_action_doc,
        "interceptedCount": total_intercepted or latest_session.get("interceptedCount", 0),
        "allowedCount": allowed_count,
        "blockedCount": blocked_count,
        "approvalCount": approval_count
    }

