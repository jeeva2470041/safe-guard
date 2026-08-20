"""
Incident & Threat Forensics API Router — Phase 3 & 4.

Provides endpoints to inspect security incidents, attack chains, blast radius,
10-point "WHY BLOCKED" forensic explanations, 5-option recovery, checkpoints, and tamper-evident audit verification.
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

from app.services.incident_manager import (
    get_incidents_by_goal,
    get_incident_by_id,
    get_forensic_explanation,
    execute_incident_recovery,
)
from app.services.checkpoint_service import (
    create_checkpoint,
    rollback_to_checkpoint,
    list_checkpoints,
    get_checkpoint_by_id,
)
from app.services.audit_service import verify_audit_chain
from app.database.connection import get_database

router = APIRouter(tags=["incidents", "recovery", "checkpoints", "audit"])


# ─── Pydantic Request Models ───────────────────────────────────

class RecoveryRequest(BaseModel):
    action: str  # CONTINUE | ABORT | ROLLBACK | EVOLVE_GOAL | START_NEW_SESSION
    checkpointId: Optional[str] = None
    evolvedGoal: Optional[str] = None
    evolvedConstraints: Optional[List[str]] = None
    changeReason: Optional[str] = None


class CheckpointCreateRequest(BaseModel):
    goalId: str
    label: Optional[str] = "Manual Checkpoint"
    metadata: Optional[Dict[str, Any]] = None


# ─── Incident Endpoints ────────────────────────────────────────

@router.get("/api/incidents/{goal_id}/summary")
async def get_goal_incident_summary(goal_id: str):
    """Fetch aggregated incident metrics, severity breakdown, and threat vectors for a goal."""
    incidents = await get_incidents_by_goal(goal_id)
    open_incidents = [inc for inc in incidents if inc.get("status") == "OPEN"]
    resolved_incidents = [inc for inc in incidents if inc.get("status") == "RESOLVED"]

    severity_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
    attack_types: Dict[str, int] = {}

    for inc in incidents:
        sev = inc.get("severity", "MEDIUM")
        severity_counts[sev] = severity_counts.get(sev, 0) + 1
        att = inc.get("attackType", "UNKNOWN")
        attack_types[att] = attack_types.get(att, 0) + 1

    return {
        "goalId": goal_id,
        "total": len(incidents),
        "open": len(open_incidents),
        "resolved": len(resolved_incidents),
        "severity": severity_counts,
        "attackTypes": attack_types,
        "hasCriticalThreat": severity_counts.get("CRITICAL", 0) > 0 and len(open_incidents) > 0
    }


@router.get("/api/incidents/{goal_id}")
async def list_goal_incidents(goal_id: str):
    """List all security incidents associated with a goal."""
    incidents = await get_incidents_by_goal(goal_id)
    return {"goalId": goal_id, "count": len(incidents), "incidents": incidents}


@router.get("/api/incidents/detail/{incident_id}")
async def get_incident_details(incident_id: str):
    """Fetch complete forensic details and attack chain graph for a specific incident."""
    incident = await get_incident_by_id(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident


@router.get("/api/incidents/{incident_id}/explanation")
async def get_incident_forensic_explanation(incident_id: str):
    """Fetch the structured 10-Point 'WHY BLOCKED' forensic explanation for an incident."""
    explanation = await get_forensic_explanation(incident_id)
    if not explanation:
        raise HTTPException(status_code=404, detail="Incident not found")
    return explanation


@router.post("/api/incidents/{incident_id}/resolve")
async def resolve_incident(incident_id: str):
    """Mark an incident as resolved by the security administrator."""
    db = get_database()
    result = await db.incidents.update_one(
        {"incidentId": incident_id},
        {"$set": {"status": "RESOLVED"}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Incident not found")
    return {"incidentId": incident_id, "status": "RESOLVED", "message": "Incident marked as resolved."}


@router.post("/api/incidents/{incident_id}/recover")
async def recover_from_incident(incident_id: str, req: RecoveryRequest):
    """
    Execute one of the 5 recovery strategies:
    - CONTINUE: Unfreeze agent & resume session
    - ABORT: Terminate agent session safely
    - ROLLBACK: Rollback sandbox files to checkpoint
    - EVOLVE_GOAL: Evolve goal policy & constraints
    - START_NEW_SESSION: Reset session state
    """
    try:
        recovery_res = await execute_incident_recovery(
            incident_id=incident_id,
            recovery_action=req.action,
            params=req.model_dump()
        )
        return recovery_res
    except ValueError as val_err:
        raise HTTPException(status_code=400, detail=str(val_err))
    except Exception as ex:
        raise HTTPException(status_code=500, detail=f"Recovery failed: {str(ex)}")


@router.post("/api/incidents/{goal_id}/unfreeze")
async def unfreeze_goal_after_incident(goal_id: str):
    """Unfreeze a goal from PAUSED status back to ACTIVE after incident containment review."""
    db = get_database()
    result = await db.goals.update_one(
        {"goalId": goal_id},
        {
            "$set": {
                "status": "ACTIVE",
                "pauseReason": None,
                "activeIncidentId": None
            }
        }
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Goal not found")
    return {"goalId": goal_id, "status": "ACTIVE", "message": "Goal unfreezed and active session unlocked."}


# ─── Checkpoint & Rollback Endpoints ───────────────────────────

@router.post("/api/checkpoints")
async def create_new_checkpoint(req: CheckpointCreateRequest):
    """Create a manual or pre-execution state checkpoint of sandbox files and goal state."""
    try:
        chk = await create_checkpoint(goal_id=req.goalId, label=req.label, metadata=req.metadata)
        return chk
    except Exception as ex:
        raise HTTPException(status_code=500, detail=f"Failed to create checkpoint: {str(ex)}")


@router.get("/api/checkpoints/{goal_id}")
async def list_goal_checkpoints(goal_id: str):
    """List all available recovery checkpoints for a goal."""
    checkpoints = await list_checkpoints(goal_id)
    return {"goalId": goal_id, "count": len(checkpoints), "checkpoints": checkpoints}


@router.post("/api/checkpoints/{checkpoint_id}/rollback")
async def rollback_sandbox_checkpoint(checkpoint_id: str, goal_id: str = Query(...)):
    """
    Safely restores sandbox workspace files and resets agent containment state to a recorded checkpoint.
    """
    try:
        res = await rollback_to_checkpoint(checkpoint_id, goal_id)
        return res
    except ValueError as val_err:
        raise HTTPException(status_code=400, detail=str(val_err))
    except Exception as ex:
        raise HTTPException(status_code=500, detail=f"Rollback failed: {str(ex)}")


# ─── Tamper-Evident Hash Chain Audit Endpoints ─────────────────

@router.get("/api/audit/verify")
async def verify_global_audit_chain():
    """
    Cryptographically verify the global tamper-evident SHA-256 audit hash chain.
    Traverses every security decision block, recalculating hashes to detect any database tampering.
    """
    res = await verify_audit_chain(goal_id=None)
    return res


@router.get("/api/audit/verify/{goal_id}")
async def verify_goal_audit_chain(goal_id: str):
    """Cryptographically verify the audit hash chain for a specific goal."""
    res = await verify_audit_chain(goal_id=goal_id)
    return res


@router.get("/api/audit/{goal_id}")
async def get_goal_audit_logs(goal_id: str):
    """Retrieve raw cryptographic audit log records with SHA-256 event hashes."""
    db = get_database()
    logs = await db.audit_logs.find({"goalId": goal_id}, {"_id": 0}).sort("chainIndex", 1).to_list(length=100)
    return {"goalId": goal_id, "count": len(logs), "auditLogs": logs}
