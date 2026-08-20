"""
Incident Management & Runtime Containment Service — Phase 3.

Manages the containment lifecycle when high-severity attacks or critical drift are detected:
1. FREEZES agent execution (sets goal status to PAUSED and locks active session)
2. BLOCKS unauthorized action execution
3. CREATES persistent incident record in MongoDB 'incidents' collection
4. CAPTURES forensic evidence, attack chain graph, and recommended remediations
"""

import uuid
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from app.database.connection import get_database

logger = logging.getLogger("agent_guard.incident_manager")


async def create_security_incident(
    goal_id: str,
    attack_type: str,
    severity: str,
    action_id: str,
    action_type: str,
    target: str,
    evidence: List[str],
    attack_chain: Optional[Dict[str, Any]] = None,
    trigger_reason: str = ""
) -> Dict[str, Any]:
    """
    Creates and records a security incident, freezing the active goal/session.
    """
    db = get_database()
    incident_id = f"INC-{uuid.uuid4().hex[:8].upper()}"
    now_iso = datetime.now(timezone.utc).isoformat()

    incident_doc = {
        "incidentId": incident_id,
        "goalId": goal_id,
        "attackType": attack_type,
        "severity": severity,
        "status": "OPEN",
        "actionId": action_id,
        "actionType": action_type,
        "target": target,
        "triggerReason": trigger_reason,
        "evidence": evidence,
        "attackChain": attack_chain,
        "containmentAction": "AGENT_FROZEN",
        "createdAt": now_iso,
        "updatedAt": now_iso
    }

    try:
        await db.incidents.insert_one(incident_doc)
        logger.warning(f"SECURITY INCIDENT CREATED: {incident_id} [{severity}] {attack_type} on goal {goal_id}")
    except Exception as err:
        logger.error(f"Failed to persist incident in MongoDB: {err}")

    # Freeze the associated goal in MongoDB
    try:
        await db.goals.update_one(
            {"goalId": goal_id},
            {
                "$set": {
                    "status": "PAUSED",
                    "pauseReason": f"Security Incident {incident_id}: {trigger_reason}",
                    "activeIncidentId": incident_id,
                    "pausedAt": now_iso
                }
            }
        )
    except Exception as err:
        logger.error(f"Failed to freeze goal {goal_id}: {err}")

    incident_doc.pop("_id", None)
    return incident_doc


async def get_incidents_by_goal(goal_id: str) -> List[Dict[str, Any]]:
    """Fetches all incident records for a specific goal."""
    db = get_database()
    incidents = await db.incidents.find({"goalId": goal_id}, {"_id": 0}).sort("createdAt", -1).to_list(length=50)
    return incidents


async def get_incident_by_id(incident_id: str) -> Optional[Dict[str, Any]]:
    """Fetches full forensic details of a single incident."""
    db = get_database()
    return await db.incidents.find_one({"incidentId": incident_id}, {"_id": 0})
