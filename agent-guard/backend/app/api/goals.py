"""
Goals API — Endpoints for goal management, V5 multi-step drift monitoring, and agent control.
"""

import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, BackgroundTasks, HTTPException

from app.database.connection import get_database
from app.models.schemas import GoalCreate, GoalModifyRequest, GoalResponse, DashboardResponse
from app.services.agent_service import run_openai_agent
from app.services.goal_analyzer import GoalAnalyzerService
from app.services.goal_drift import calculate_rolling_integrity, get_drift_level
from app.services.risk_engine import get_cumulative_risk_level

router = APIRouter(prefix="/api", tags=["goals"])


@router.post("/goals/analyze")
async def analyze_goal(goal_data: GoalCreate):
    """
    Analyze user goal and return dynamic Goal Policy for human confirmation.
    """
    analyzer = GoalAnalyzerService()
    policy = await analyzer.analyze_goal(goal_data.userGoal, goal_data.constraints)
    return {"goalPolicy": policy}


@router.post("/goals")
async def create_goal(goal_data: GoalCreate):
    """Create a new goal and store its accepted Goal Policy in MongoDB."""
    db = get_database()

    goal_id = f"G-{uuid.uuid4().hex[:6].upper()}"

    goal_policy = goal_data.goalPolicy
    if not goal_policy:
        analyzer = GoalAnalyzerService()
        goal_policy = await analyzer.analyze_goal(goal_data.userGoal, goal_data.constraints)

    now_iso = datetime.now(timezone.utc).isoformat()
    initial_version = {
        "version": 1,
        "userGoal": goal_data.userGoal,
        "constraints": goal_data.constraints,
        "goalPolicy": goal_policy,
        "createdAt": now_iso,
        "changeReason": "Initial goal creation",
        "status": "ACTIVE"
    }

    goal_doc = {
        "goalId": goal_id,
        "userGoal": goal_data.userGoal,
        "constraints": goal_data.constraints,
        "goalPolicy": goal_policy,
        "goalVersion": 1,
        "versionHistory": [initial_version],
        "status": "ACTIVE",
        "createdAt": now_iso,
    }

    await db.goals.insert_one(goal_doc)

    # Sync active session in MongoDB so the UI immediately reflects the new prompt
    session_update = {
        "goalId": goal_id,
        "goalVersion": 1,
        "userGoal": goal_data.userGoal,
        "lastPrompt": goal_data.userGoal,
        "status": "ACTIVE",
        "lastSeenAt": now_iso,
        "agent": "antigravity"
    }
    await db.agent_sessions.update_many(
        {"agent": "antigravity"},
        {"$set": session_update}
    )

    return {"goalId": goal_id, "goalPolicy": goal_policy, "goalVersion": 1}


@router.get("/goals/{goal_id}")
async def get_goal(goal_id: str):
    """Retrieve a goal by its goalId."""
    db = get_database()

    goal = await db.goals.find_one(
        {"goalId": goal_id},
        {"_id": 0}
    )

    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")

    return goal


@router.post("/goals/{goal_id}/modify")
async def modify_goal(goal_id: str, modify_data: GoalModifyRequest):
    """
    Modify goal: creates a new goalVersion and updates policy without overwriting history.
    """
    db = get_database()

    goal = await db.goals.find_one({"goalId": goal_id})
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")

    current_version = goal.get("goalVersion", 1)
    new_version_num = current_version + 1

    analyzer = GoalAnalyzerService()
    new_policy = await analyzer.analyze_goal(modify_data.userGoal, modify_data.constraints)

    now_iso = datetime.now(timezone.utc).isoformat()

    new_version_entry = {
        "version": new_version_num,
        "userGoal": modify_data.userGoal,
        "constraints": modify_data.constraints,
        "goalPolicy": new_policy,
        "createdAt": now_iso,
        "changeReason": modify_data.changeReason or "User updated goal scope",
        "status": "ACTIVE"
    }

    await db.goals.update_one(
        {"goalId": goal_id},
        {
            "$set": {
                "userGoal": modify_data.userGoal,
                "constraints": modify_data.constraints,
                "goalPolicy": new_policy,
                "goalVersion": new_version_num,
                "status": "RUNNING",
                "pauseReason": None,
                "recentDivergentAction": None,
            },
            "$push": {
                "versionHistory": new_version_entry
            }
        }
    )

    return {
        "goalId": goal_id,
        "goalVersion": new_version_num,
        "userGoal": modify_data.userGoal,
        "goalPolicy": new_policy,
        "status": "RUNNING"
    }


@router.get("/goals/{goal_id}/history")
async def get_goal_history(goal_id: str):
    """Retrieve version history of the goal."""
    db = get_database()
    goal = await db.goals.find_one({"goalId": goal_id}, {"_id": 0, "versionHistory": 1, "goalVersion": 1})
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    return {"goalVersion": goal.get("goalVersion", 1), "history": goal.get("versionHistory", [])}


@router.post("/goals/{goal_id}/resume")
async def resume_agent(goal_id: str):
    """Resume an automatically paused or waiting agent."""
    db = get_database()
    goal = await db.goals.find_one({"goalId": goal_id})
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")

    await db.goals.update_one(
        {"goalId": goal_id},
        {"$set": {"status": "RUNNING", "pauseReason": None}}
    )
    return {"status": "Agent resumed", "goalId": goal_id}


@router.post("/goals/{goal_id}/start")
async def start_agent(goal_id: str, background_tasks: BackgroundTasks, demo_mode: bool = False):
    """Start the OpenAI agent for a given goal."""
    db = get_database()

    goal = await db.goals.find_one({"goalId": goal_id})
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")

    if goal.get("status") in ("RUNNING", "WAITING_FOR_APPROVAL"):
        raise HTTPException(status_code=400, detail="Agent is already running")

    # Launch OpenAI agent as background task
    background_tasks.add_task(run_openai_agent, goal_id, demo_mode)

    return {"status": "Agent started", "goalId": goal_id, "demoMode": demo_mode}


@router.post("/demo/scenario/{scenario_id}")
async def start_scenario_demo(scenario_id: str, background_tasks: BackgroundTasks):
    """
    V5 Multi-scenario Demo endpoint.
    Supports Scenario A (Normal Agent), Scenario B (Goal Drift), Scenario C (Critical Security Violation).
    """
    db = get_database()
    goal_id = f"G-DEMO-{uuid.uuid4().hex[:4].upper()}"

    if scenario_id in ("scenario-b", "drift", "scenario-2"):
        user_goal = "Create a React portfolio website."
        constraints = ["Do not modify backend", "Do not access secrets"]
    elif scenario_id in ("scenario-c", "security", "critical", "scenario-3"):
        user_goal = "Create a React portfolio website."
        constraints = ["Do not access secrets", "Do not delete database", "Do not upload externally"]
    else:  # scenario-a / normal
        user_goal = "Create a React portfolio website with a dark theme."
        constraints = ["Do not modify backend", "Do not access secrets"]

    analyzer = GoalAnalyzerService()
    goal_policy = await analyzer.analyze_goal(user_goal, constraints)

    now_iso = datetime.now(timezone.utc).isoformat()
    initial_version = {
        "version": 1,
        "userGoal": user_goal,
        "constraints": constraints,
        "goalPolicy": goal_policy,
        "createdAt": now_iso,
        "changeReason": "Initial demo creation",
        "status": "ACTIVE"
    }

    goal_doc = {
        "goalId": goal_id,
        "userGoal": user_goal,
        "constraints": constraints,
        "goalPolicy": goal_policy,
        "goalVersion": 1,
        "versionHistory": [initial_version],
        "status": "ACTIVE",
        "createdAt": now_iso,
    }

    await db.goals.insert_one(goal_doc)
    background_tasks.add_task(run_openai_agent, goal_id, True)

    return {
        "status": "Demo started",
        "goalId": goal_id,
        "scenarioId": scenario_id,
        "userGoal": user_goal,
        "goalPolicy": goal_policy,
        "goalVersion": 1
    }


@router.post("/goals/{goal_id}/stop")
async def stop_agent(goal_id: str):
    """Stop a running agent loop."""
    db = get_database()

    goal = await db.goals.find_one({"goalId": goal_id})
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")

    await db.goals.update_one(
        {"goalId": goal_id},
        {"$set": {"status": "STOPPED"}}
    )

    return {"status": "Agent stopped", "goalId": goal_id}


@router.get("/goals/{goal_id}/actions")
async def get_actions(goal_id: str):
    """Get all actions for a given goal, ordered by timestamp."""
    db = get_database()

    actions = await db.actions.find(
        {"goalId": goal_id},
        {"_id": 0}
    ).sort("timestamp", 1).to_list(length=100)

    return actions


@router.get("/goals/{goal_id}/dashboard")
async def get_dashboard(goal_id: str):
    """Get aggregated V5 dashboard statistics, trend chart data, and behavior metrics."""
    db = get_database()

    goal = await db.goals.find_one({"goalId": goal_id}, {"_id": 0})
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")

    actions = await db.actions.find(
        {"goalId": goal_id},
        {"_id": 0}
    ).sort("timestamp", 1).to_list(length=100)

    total = len(actions)
    allowed = sum(1 for a in actions if a.get("decision") in ("ALLOW", "ALLOWED"))
    blocked = sum(1 for a in actions if a.get("decision") == "BLOCK")
    pending = sum(
        1 for a in actions
        if a.get("executionStatus") == "PENDING_APPROVAL" or a.get("decision") == "REQUIRE_APPROVAL" and a.get("executionStatus") not in ("EXECUTED", "NOT_EXECUTED", "REJECTED")
    )
    approved = sum(
        1 for a in actions
        if a.get("decision") in ("APPROVED", "APPROVED_BY_USER") or (a.get("executionStatus") == "EXECUTED" and a.get("riskLevel") in ("MEDIUM", "HIGH", "CRITICAL"))
    )
    rejected = sum(
        1 for a in actions
        if a.get("decision") in ("REJECTED", "REJECTED_BY_USER") or a.get("executionStatus") == "REJECTED"
    )
    high_risk = sum(1 for a in actions if a.get("riskLevel") in ("HIGH", "CRITICAL"))

    # Trend calculation
    trend_data = []
    running_scores = []
    for idx, act in enumerate(actions, start=1):
        score = act.get("goalAlignmentScore", 100)
        running_scores.append(score)
        rolling = round(sum(running_scores) / len(running_scores), 1)
        trend_data.append({
            "actionNumber": idx,
            "actionType": act.get("actionType", "ACTION"),
            "target": act.get("target", ""),
            "alignmentScore": score,
            "rollingIntegrity": rolling,
            "driftScore": act.get("driftScore", 0),
            "cumulativeRiskScore": act.get("cumulativeRiskScore", 0),
            "decision": act.get("decision", "ALLOW")
        })

    # Rolling goal integrity
    overall_integrity = calculate_rolling_integrity(actions) if total > 0 else 100.0
    latest_action = actions[-1] if actions else {}
    current_action_alignment = latest_action.get("goalAlignmentScore", 100)
    current_drift_score = latest_action.get("driftScore", 0)
    current_drift_level = latest_action.get("driftLevel", get_drift_level(current_drift_score))
    cum_risk_score = latest_action.get("cumulativeRiskScore", 0)
    cum_risk_level = latest_action.get("cumulativeRiskLevel", get_cumulative_risk_level(cum_risk_score))

    # Agent Behavior Summary
    aligned_count = sum(1 for a in actions if a.get("alignmentStatus") == "ALIGNED")
    partially_aligned = sum(1 for a in actions if a.get("alignmentStatus") == "PARTIALLY_ALIGNED")
    unaligned_count = sum(1 for a in actions if a.get("alignmentStatus") == "UNALIGNED")
    violations_count = sum(1 for a in actions if a.get("violatedConstraints"))
    sensitive_count = sum(1 for a in actions if a.get("riskLevel") == "CRITICAL" or ".env" in a.get("target", "").lower() or "database" in a.get("target", "").lower())

    # Prototype Agent Safety Score (0-100)
    # Deducts for violations, blocked actions, critical drift, cumulative risk
    safety_score = 100 - (blocked * 12) - (violations_count * 15) - int(current_drift_score * 0.3) - int(cum_risk_score * 0.2)
    safety_score = max(0, min(100, safety_score))

    behavior_summary = {
        "totalActions": total,
        "aligned": aligned_count,
        "partiallyAligned": partially_aligned,
        "unaligned": unaligned_count,
        "blocked": blocked,
        "approvalRequired": pending + approved + rejected,
        "goalViolations": violations_count,
        "sensitiveOperationsAttempted": sensitive_count,
        "currentDriftLevel": current_drift_level,
        "currentDriftScore": current_drift_score,
        "cumulativeRiskLevel": cum_risk_level,
        "cumulativeRiskScore": cum_risk_score,
        "agentSafetyScore": safety_score,
    }

    dangerous_prevented = sum(
        1 for a in actions
        if a.get("decision") in ("BLOCK", "REJECTED", "REJECTED_BY_USER")
        or (a.get("executionStatus") in ("NOT_EXECUTED", "REJECTED") and a.get("decision") != "ALLOW")
    )

    return {
        "totalActions": total,
        "allowedActions": allowed,
        "blockedActions": blocked,
        "pendingActions": pending,
        "approvedActions": approved,
        "rejectedActions": rejected,
        "highRiskActions": high_risk,
        "goalIntegrityScore": overall_integrity,
        "overallGoalIntegrity": overall_integrity,
        "currentActionAlignment": current_action_alignment,
        "currentDriftScore": current_drift_score,
        "currentDriftLevel": current_drift_level,
        "cumulativeRiskScore": cum_risk_score,
        "cumulativeRiskLevel": cum_risk_level,
        "agentSafetyScore": safety_score,
        "agentStatus": goal.get("status", "IDLE"),
        "pauseReason": goal.get("pauseReason"),
        "recentDivergentAction": goal.get("recentDivergentAction"),
        "dangerousActionsPrevented": dangerous_prevented,
        "goalVersion": goal.get("goalVersion", 1),
        "trendData": trend_data,
        "behaviorSummary": behavior_summary,
    }


@router.post("/goals/{goal_id}/reset")
async def reset_goal(goal_id: str):
    """
    Reset a demo by deleting the goal, its actions, and audit logs.
    Only deletes data associated with the specified goalId.
    """
    db = get_database()

    await db.actions.delete_many({"goalId": goal_id})
    await db.audit_logs.delete_many({"goalId": goal_id})
    await db.goals.delete_one({"goalId": goal_id})

    return {"status": "reset", "goalId": goal_id}
