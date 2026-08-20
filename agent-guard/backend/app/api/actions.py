"""
Actions API — Endpoints for approving, rejecting, and inspecting contextual action approval requests.
Supports Phase 2: Approve Once, Approve Similar Actions (Session Whitelist), Reject, and Abort.
"""

from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, HTTPException, Body

from app.database.connection import get_database
from app.services.audit_service import create_audit_log
from app.models.schemas import ApproveActionRequest

router = APIRouter(prefix="/api", tags=["actions"])


@router.get("/actions/{action_id}")
async def get_action_status(action_id: str):
    """Fetch status of an action (useful for polling pending approvals)."""
    db = get_database()
    action = await db.actions.find_one({"actionId": action_id}, {"_id": 0})
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")
    return action


@router.get("/actions/{action_id}/approval-request")
async def get_contextual_approval_request(action_id: str):
    """
    Get formatted contextual approval request for human-in-the-loop review.
    Provides complete intent context, goal relationship, reversibility, and consequence.
    """
    db = get_database()
    action = await db.actions.find_one({"actionId": action_id}, {"_id": 0})
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")

    goal = await db.goals.find_one({"goalId": action.get("goalId")}, {"_id": 0})

    return {
        "actionId": action_id,
        "goalId": action.get("goalId"),
        "action": f"{action.get('actionType')} on {action.get('target')}",
        "actionType": action.get("actionType"),
        "target": action.get("target"),
        "description": action.get("description"),
        "goal": goal.get("userGoal") if goal else "Active user goal",
        "goalAlignment": action.get("goalAlignmentScore", 100),
        "goalRelationship": action.get("goalRelationship", "DIRECTLY_RELEVANT"),
        "reason": action.get("reason", "Requires human authorization"),
        "destination": action.get("target"),
        "reversibility": action.get("reversibility", "REVERSIBLE"),
        "consequenceLevel": action.get("consequenceLevel", "HIGH"),
        "riskLevel": action.get("riskLevel", "HIGH"),
        "decision": action.get("decision", "REQUIRE_APPROVAL"),
        "executionStatus": action.get("executionStatus", "PENDING_APPROVAL"),
        "supportedModes": ["ONCE", "SIMILAR", "REJECT", "ABORT"]
    }


@router.post("/actions/{action_id}/approve")
async def approve_action(
    action_id: str,
    body: Optional[ApproveActionRequest] = None
):
    """
    Approve an action that requires user approval.
    Supports approval modes:
    - ONCE: Approves only this single action instance.
    - SIMILAR: Approves this instance and creates a session-level whitelist for subsequent matching actions.
    """
    db = get_database()
    mode = body.approvalMode.upper() if body and body.approvalMode else "ONCE"
    reason = body.reason if body and body.reason else "User manually approved the action after review."

    action = await db.actions.find_one({"actionId": action_id})
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")

    if action.get("executionStatus") not in ("PENDING_APPROVAL", "WAITING_FOR_APPROVAL") and action.get("decision") != "REQUIRE_APPROVAL":
        # If already executed or not requiring approval, return current status
        return {
            "status": "already_resolved",
            "actionId": action_id,
            "decision": action.get("decision"),
            "mode": mode
        }

    goal_id = action.get("goalId")

    # Update the action: mark as approved and executed
    await db.actions.update_one(
        {"actionId": action_id},
        {
            "$set": {
                "decision": "APPROVED",
                "executionStatus": "EXECUTED",
                "approvalMode": mode,
                "approvedAt": datetime.now(timezone.utc).isoformat(),
            }
        }
    )

    # If SIMILAR mode selected, whitelist this action type in active goal session
    if mode == "SIMILAR" and goal_id:
        pattern = {
            "actionType": action.get("actionType"),
            "target": action.get("target"),
            "approvedAt": datetime.now(timezone.utc).isoformat()
        }
        await db.goals.update_one(
            {"goalId": goal_id},
            {"$addToSet": {"approvedSimilarActions": pattern}}
        )

    # Resume goal status if it was waiting for approval
    if goal_id:
        await db.goals.update_one(
            {"goalId": goal_id, "status": "WAITING_FOR_APPROVAL"},
            {"$set": {"status": "RUNNING"}}
        )

    # Create audit log for the approval
    await create_audit_log(
        goal_id=goal_id or "default-goal",
        action_id=action_id,
        decision="APPROVED",
        risk_level=action.get("riskLevel", "UNKNOWN"),
        reason=f"User approved action with mode '{mode}': {reason}",
    )

    return {
        "status": "approved",
        "actionId": action_id,
        "mode": mode,
        "executionStatus": "EXECUTED"
    }


@router.post("/actions/{action_id}/reject")
async def reject_action(
    action_id: str,
    body: Optional[ApproveActionRequest] = None
):
    """Reject an action that requires user approval."""
    db = get_database()
    reason = body.reason if body and body.reason else "User rejected the action after review."

    action = await db.actions.find_one({"actionId": action_id})
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")

    # Update the action: mark as rejected and not executed
    await db.actions.update_one(
        {"actionId": action_id},
        {
            "$set": {
                "decision": "REJECTED",
                "executionStatus": "NOT_EXECUTED",
                "rejectedAt": datetime.now(timezone.utc).isoformat(),
            }
        }
    )

    # Create audit log for the rejection
    await create_audit_log(
        goal_id=action.get("goalId", "default-goal"),
        action_id=action_id,
        decision="REJECTED",
        risk_level=action.get("riskLevel", "UNKNOWN"),
        reason=f"User rejected the action: {reason}",
    )

    return {
        "status": "rejected",
        "actionId": action_id,
        "executionStatus": "NOT_EXECUTED"
    }
