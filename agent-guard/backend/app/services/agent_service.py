"""
Agent Service — OpenAI-powered Agent Loop Orchestrator.

Manages the autonomous execution loop for OpenAI agent proposals.
Enforces the Security Gateway pipeline on EVERY proposed action:
Goal Integrity → Risk Engine → Authorization Engine → Tool Execution / Human Approval / Security Block
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional

from app.database.connection import get_database
from app.services.openai_agent import OpenAIAgentService
from app.services.security_gateway import authorize_and_execute
from app.services.execution_verifier import verify_action_execution
from app.tools.tool_registry import dispatch_tool_execution

logger = logging.getLogger("agent_guard.agent_service")

AGENT_ID = "OPENAI-AGENT-001"
MAX_AGENT_ACTIONS = 15
ACTION_DELAY_SECONDS = 2.0


async def run_openai_agent(goal_id: str, demo_mode: bool = False):
    """
    Run the OpenAI agent loop for a given goal.
    Proposes actions one by one and routes them strictly through the Security Gateway.
    """
    db = get_database()

    goal = await db.goals.find_one({"goalId": goal_id})
    if not goal:
        logger.error(f"Goal {goal_id} not found.")
        return

    user_goal = goal["userGoal"]
    constraints = goal.get("constraints", [])

    openai_service = OpenAIAgentService()

    await db.goals.update_one(
        {"goalId": goal_id},
        {"$set": {"status": "RUNNING"}}
    )

    action_history = []
    action_counter = 0

    while action_counter < MAX_AGENT_ACTIONS:
        current_goal = await db.goals.find_one({"goalId": goal_id})
        if not current_goal or current_goal.get("status") == "STOPPED":
            logger.info(f"Goal {goal_id} stopped or cancelled.")
            break

        # ── Step 1: Ask OpenAI Agent for Next Action Proposal ──
        proposal = await openai_service.propose_next_action(
            user_goal=user_goal,
            constraints=constraints,
            previous_actions=action_history,
            demo_mode=demo_mode,
            step_index=action_counter,
            goal_policy=current_goal.get("goalPolicy") if current_goal else None
        )

        action_type = proposal.get("action_type", "READ_FILE").upper()
        target = proposal.get("target", "Login.jsx")
        description = proposal.get("description", "")

        if action_type == "COMPLETE" or target == "goal":
            await db.goals.update_one(
                {"goalId": goal_id},
                {"$set": {"status": "COMPLETED"}}
            )
            break

        action_counter += 1

        # ── Step 2: Route Proposal through Security Gateway ──
        action_doc = await authorize_and_execute(
            goal_id=goal_id,
            action_type=action_type,
            target=target,
            description=description,
            agent_id=AGENT_ID
        )

        action_id = action_doc["actionId"]
        decision = action_doc["decision"]
        pause_triggered = action_doc.get("pauseTriggered", False)

        # ── Step 3: Handle Automatic Security PAUSE ──
        if pause_triggered:
            logger.warning(f"Agent automatic security pause triggered for Goal {goal_id}: {action_doc.get('pauseReason')}")
            # Poll until user resumes or stops
            while True:
                await asyncio.sleep(1.0)
                g_check = await db.goals.find_one({"goalId": goal_id})
                if not g_check:
                    break
                g_status = g_check.get("status")
                if g_status in ("STOPPED", "FAILED", "COMPLETED"):
                    break
                if g_status in ("RUNNING", "ACTIVE"):
                    # User clicked RESUME or MODIFIED GOAL! Reload goal & constraints
                    user_goal = g_check.get("userGoal", user_goal)
                    constraints = g_check.get("constraints", constraints)
                    logger.info(f"Goal {goal_id} resumed/updated by user to: {user_goal}")
                    break

            if g_status == "STOPPED":
                break

        # ── Step 4: Handle REQUIRE_APPROVAL Pausing & Approval Execution ──
        elif decision == "REQUIRE_APPROVAL":
            await db.goals.update_one(
                {"goalId": goal_id},
                {"$set": {"status": "WAITING_FOR_APPROVAL"}}
            )

            # Poll MongoDB until user responds (Approve/Reject)
            timeout = 300
            elapsed = 0
            poll_interval = 1.0

            updated_action = None
            while elapsed < timeout:
                await asyncio.sleep(poll_interval)
                elapsed += poll_interval

                updated_action = await db.actions.find_one({"actionId": action_id})
                if updated_action:
                    status_in_db = updated_action.get("executionStatus")
                    if status_in_db in ("EXECUTED", "REJECTED", "NOT_EXECUTED"):
                        break

            if updated_action and updated_action.get("executionStatus") == "EXECUTED":
                # Execute tool post-approval
                tool_out = dispatch_tool_execution(action_type, target, description)
                verifier = verify_action_execution(action_type, target, "APPROVED", "EXECUTED")

                await db.actions.update_one(
                    {"actionId": action_id},
                    {
                        "$set": {
                            "toolOutput": tool_out,
                            "verificationStatus": verifier["verificationStatus"],
                            "verificationMessage": verifier["verificationMessage"],
                        }
                    }
                )

                action_history.append({
                    "actionType": action_type,
                    "target": target,
                    "description": description,
                    "decision": "APPROVED",
                    "executionStatus": "EXECUTED",
                    "toolOutput": tool_out
                })
            else:
                action_history.append({
                    "actionType": action_type,
                    "target": target,
                    "description": description,
                    "decision": "REJECTED",
                    "executionStatus": "NOT_EXECUTED",
                    "reason": "The user rejected this action after human approval review."
                })

            current_check = await db.goals.find_one({"goalId": goal_id})
            if current_check and current_check.get("status") not in ("PAUSED", "STOPPED"):
                await db.goals.update_one(
                    {"goalId": goal_id},
                    {"$set": {"status": "RUNNING"}}
                )

        elif decision == "ALLOW":
            action_history.append({
                "actionType": action_type,
                "target": target,
                "description": description,
                "decision": "ALLOW",
                "executionStatus": "EXECUTED",
                "toolOutput": action_doc.get("toolOutput")
            })

        elif decision == "BLOCK":
            action_history.append({
                "actionType": action_type,
                "target": target,
                "description": description,
                "decision": "BLOCK",
                "executionStatus": "NOT_EXECUTED",
                "reason": "The proposed action was blocked by the security policy because it is destructive and/or unrelated to the user's goal."
            })

        await asyncio.sleep(ACTION_DELAY_SECONDS)

    final_goal = await db.goals.find_one({"goalId": goal_id})
    if final_goal and final_goal.get("status") not in ("STOPPED", "FAILED", "PAUSED"):
        await db.goals.update_one(
            {"goalId": goal_id},
            {"$set": {"status": "COMPLETED"}}
        )

