"""
Actions API — Endpoints for approving/rejecting actions that require approval.
"""

from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException

from app.database.connection import get_database
from app.services.audit_service import create_audit_log

router = APIRouter(prefix="/api", tags=["actions"])


@router.get("/actions/{action_id}")
async def get_action_status(action_id: str):
    """Fetch status of an action (useful for polling pending approvals)."""
    db = get_database()
    action = await db.actions.find_one({"actionId": action_id})
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")
    return {
        "actionId": action_id,
        "goalId": action.get("goalId"),
        "decision": action.get("decision"),
        "executionStatus": action.get("executionStatus"),
        "riskLevel": action.get("riskLevel"),
        "reason": action.get("reason"),
    }



@router.post("/actions/{action_id}/approve")
async def approve_action(action_id: str):
    """Approve an action that requires user approval."""
    db = get_database()

    action = await db.actions.find_one({"actionId": action_id})
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")

    if action.get("executionStatus") != "PENDING_APPROVAL":
        raise HTTPException(
            status_code=400,
            detail=f"Action is not pending approval. Current status: {action.get('executionStatus')}"
        )

    # Update the action: mark as approved and executed
    await db.actions.update_one(
        {"actionId": action_id},
        {
            "$set": {
                "decision": "APPROVED",
                "executionStatus": "EXECUTED",
                "approvedAt": datetime.now(timezone.utc).isoformat(),
            }
        }
    )

    # Create audit log for the approval
    await create_audit_log(
        goal_id=action["goalId"],
        action_id=action_id,
        decision="APPROVED",
        risk_level=action.get("riskLevel", "UNKNOWN"),
        reason="User manually approved the action after review.",
    )

    return {"status": "approved", "actionId": action_id}


@router.post("/actions/{action_id}/reject")
async def reject_action(action_id: str):
    """Reject an action that requires user approval."""
    db = get_database()

    action = await db.actions.find_one({"actionId": action_id})
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")

    if action.get("executionStatus") != "PENDING_APPROVAL":
        raise HTTPException(
            status_code=400,
            detail=f"Action is not pending approval. Current status: {action.get('executionStatus')}"
        )

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
        goal_id=action["goalId"],
        action_id=action_id,
        decision="REJECTED",
        risk_level=action.get("riskLevel", "UNKNOWN"),
        reason="User rejected the action after review.",
    )

    return {"status": "rejected", "actionId": action_id}
