"""
Incident & Threat Forensics API Router — Phase 3.
Provides endpoints to inspect security incidents, attack chains, and containment states.
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any, Optional
from app.services.incident_manager import get_incidents_by_goal, get_incident_by_id
from app.database.connection import get_database

router = APIRouter(prefix="/api/incidents", tags=["incidents"])


@router.get("/{goal_id}/summary")
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


@router.get("/{goal_id}")
async def list_goal_incidents(goal_id: str):
    """List all security incidents associated with a goal."""
    incidents = await get_incidents_by_goal(goal_id)
    return {"goalId": goal_id, "count": len(incidents), "incidents": incidents}


@router.get("/detail/{incident_id}")
async def get_incident_details(incident_id: str):
    """Fetch complete forensic details and attack chain graph for a specific incident."""
    incident = await get_incident_by_id(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident


@router.post("/{incident_id}/resolve")
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


@router.post("/{goal_id}/unfreeze")
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

