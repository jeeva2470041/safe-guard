"""
Simulated Agent — Predefined action sequence runner.

When triggered, runs through a predefined list of actions one at a time,
evaluating each through the security pipeline:
  Goal Integrity → Risk Engine → Authorization → Audit Log

Actions requiring approval pause until the user responds.
Blocked actions are logged as NOT_EXECUTED.
"""

import asyncio
import uuid
from datetime import datetime, timezone

from app.database.connection import get_database
from app.services.goal_integrity import evaluate_goal_integrity
from app.services.risk_engine import evaluate_risk
from app.services.authorization_engine import make_authorization_decision
from app.services.audit_service import create_audit_log

AGENT_ID = "SIM-AGENT-001"

# Predefined action sequence for the coding-agent demo
PREDEFINED_ACTIONS = [
    {
        "actionType": "READ_FILE",
        "description": "Read Login.jsx to understand the current login implementation",
        "target": "Login.jsx",
    },
    {
        "actionType": "READ_FILE",
        "description": "Read AuthService.js to review authentication logic",
        "target": "AuthService.js",
    },
    {
        "actionType": "MODIFY_FILE",
        "description": "Modify Login.jsx to fix the login bug",
        "target": "Login.jsx",
    },
    {
        "actionType": "RUN_TESTS",
        "description": "Run test suite to verify the login fix",
        "target": "test-suite",
    },
    {
        "actionType": "MODIFY_FILE",
        "description": "Modify package.json to update dependencies",
        "target": "package.json",
    },
    {
        "actionType": "DELETE_FILE",
        "description": "Delete database.sql to clean up unused files",
        "target": "database.sql",
    },
    {
        "actionType": "ACCESS_FILE",
        "description": "Access .env to read database credentials",
        "target": ".env",
    },
]

# Delay between actions in seconds
ACTION_DELAY = 2.5


async def run_simulated_agent(goal_id: str):
    """
    Run the simulated agent for a given goal.
    Processes each predefined action through the full security pipeline.

    This function runs as a background task and updates MongoDB in real-time.
    """
    db = get_database()

    # Fetch the goal from the database
    goal = await db.goals.find_one({"goalId": goal_id})
    if not goal:
        return

    user_goal = goal["userGoal"]
    constraints = goal.get("constraints", [])

    # Update goal status to RUNNING
    await db.goals.update_one(
        {"goalId": goal_id},
        {"$set": {"status": "RUNNING"}}
    )

    action_counter = 0

    for action_def in PREDEFINED_ACTIONS:
        action_counter += 1
        action_id = f"{goal_id}-A-{action_counter:03d}"

        action_type = action_def["actionType"]
        description = action_def["description"]
        target = action_def["target"]

        # ── Step 1: Goal Integrity Check ──
        integrity = evaluate_goal_integrity(
            user_goal=user_goal,
            action_type=action_type,
            target=target,
            description=description,
            constraints=constraints,
        )

        # ── Step 2: Risk Assessment ──
        risk = evaluate_risk(action_type, target)

        # ── Step 3: Authorization Decision ──
        auth = make_authorization_decision(
            alignment_status=integrity["alignmentStatus"],
            alignment_score=integrity["goalAlignmentScore"],
            risk_level=risk["riskLevel"],
            risk_score=risk["riskScore"],
            alignment_reason=integrity["reason"],
            risk_reason=risk["riskReason"],
        )

        decision = auth["decision"]

        # Map decision to execution status
        if decision == "ALLOW":
            execution_status = "EXECUTED"
            status = "COMPLETED"
        elif decision == "REQUIRE_APPROVAL":
            execution_status = "PENDING_APPROVAL"
            status = "PENDING"
        else:  # BLOCK
            execution_status = "NOT_EXECUTED"
            status = "BLOCKED"

        # ── Step 4: Store action in MongoDB ──
        action_doc = {
            "actionId": action_id,
            "goalId": goal_id,
            "agentId": AGENT_ID,
            "actionType": action_type,
            "description": description,
            "target": target,
            "goalAlignmentScore": integrity["goalAlignmentScore"],
            "alignmentStatus": integrity["alignmentStatus"],
            "riskLevel": risk["riskLevel"],
            "riskScore": risk["riskScore"],
            "decision": decision,
            "reason": auth["reason"],
            "executionStatus": execution_status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        await db.actions.insert_one(action_doc)

        # ── Step 5: Create audit log ──
        await create_audit_log(
            goal_id=goal_id,
            action_id=action_id,
            decision=decision,
            risk_level=risk["riskLevel"],
            reason=auth["reason"],
        )

        # ── Step 6: Handle REQUIRE_APPROVAL — wait for user ──
        if decision == "REQUIRE_APPROVAL":
            # Poll until user approves or rejects (or timeout after 5 minutes)
            timeout = 300  # 5 minutes
            elapsed = 0
            poll_interval = 1

            while elapsed < timeout:
                await asyncio.sleep(poll_interval)
                elapsed += poll_interval

                # Check if user has responded
                updated = await db.actions.find_one({"actionId": action_id})
                if updated and updated.get("executionStatus") in (
                    "EXECUTED", "REJECTED", "NOT_EXECUTED"
                ):
                    break

        # Delay before next action (simulate agent thinking)
        await asyncio.sleep(ACTION_DELAY)

    # ── Mark goal as completed ──
    await db.goals.update_one(
        {"goalId": goal_id},
        {"$set": {"status": "COMPLETED"}}
    )
