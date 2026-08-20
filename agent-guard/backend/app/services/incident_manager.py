"""
Incident Management & Runtime Containment Service — Phase 4.

Manages the full autonomous containment and recovery lifecycle:
1. FREEZES agent execution (sets goal status to PAUSED and locks active session)
2. BLOCKS unauthorized action execution
3. CREATES persistent forensic incident records in MongoDB 'incidents' collection with Blast Radius
4. PROVIDES 10-Point "WHY BLOCKED" forensic explanations
5. EXECUTES 5-Option recovery workflows (Continue, Abort, Rollback Checkpoint, Evolve Goal, New Session)
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
    trigger_reason: str = "",
    blast_radius: Optional[Dict[str, Any]] = None,
    previous_actions: Optional[List[Dict[str, Any]]] = None,
    user_goal: Optional[str] = None,
    goal_version: int = 1,
    source: str = "AGENT_PLAN",
    alignment_score: int = 0,
    source_trust: str = "UNTRUSTED",
    risk_level: str = "CRITICAL"
) -> Dict[str, Any]:
    """
    Creates and records a forensic security incident, capturing full kill chain and blast radius.
    """
    db = get_database()
    incident_id = f"INC-{uuid.uuid4().hex[:8].upper()}"
    now_iso = datetime.now(timezone.utc).isoformat()

    # Fetch goal document if user_goal missing
    if not user_goal:
        goal_doc = await db.goals.find_one({"goalId": goal_id})
        if goal_doc:
            user_goal = goal_doc.get("userGoal", "Active Agent Task")
            goal_version = goal_doc.get("goalVersion", 1)

    # Sanitize previous actions snapshot (take last 6)
    history_snapshot = []
    if previous_actions:
        for a in previous_actions[-6:]:
            history_snapshot.append({
                "actionId": a.get("actionId"),
                "actionType": a.get("actionType"),
                "target": a.get("target"),
                "decision": a.get("decision"),
                "goalAlignmentScore": a.get("goalAlignmentScore", 100),
                "riskLevel": a.get("riskLevel", "LOW")
            })

    recovery_options = [
        "CONTINUE",
        "ABORT",
        "ROLLBACK_CHECKPOINT",
        "EVOLVE_GOAL",
        "START_NEW_SESSION"
    ]

    incident_doc = {
        "incidentId": incident_id,
        "sessionId": goal_id,
        "goalId": goal_id,
        "userGoal": user_goal or "Autonomous Agent Goal",
        "goalVersion": goal_version,
        "attackType": attack_type,
        "severity": severity,
        "status": "OPEN",
        "actionId": action_id,
        "actionType": action_type,
        "target": target,
        "source": source,
        "sourceTrust": source_trust,
        "alignmentScore": alignment_score,
        "riskLevel": risk_level,
        "triggerReason": trigger_reason,
        "evidence": evidence,
        "attackChain": attack_chain,
        "blastRadius": blast_radius,
        "previousActionsSnapshot": history_snapshot,
        "containmentAction": "AGENT_FROZEN",
        "availableRecoveryOptions": recovery_options,
        "resolution": None,
        "createdAt": now_iso,
        "updatedAt": now_iso
    }

    try:
        await db.incidents.insert_one(incident_doc)
        logger.warning(f"SECURITY INCIDENT RECORDED: {incident_id} [{severity}] {attack_type} on goal {goal_id}")
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
                    "pausedAt": now_iso,
                    "recentDivergentAction": f"{action_type} on {target}"
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


async def get_forensic_explanation(incident_id: str) -> Optional[Dict[str, Any]]:
    """
    Generates the structured 10-Point "WHY BLOCKED" forensic explanation for an incident.
    """
    incident = await get_incident_by_id(incident_id)
    if not incident:
        return None

    # Derive trajectory summary from attack chain or evidence
    attack_chain = incident.get("attackChain") or {}
    chain_nodes = attack_chain.get("nodes", [])
    if chain_nodes:
        trajectory_str = " → ".join(n.get("roleInAttack", n.get("actionType", "Action")) for n in chain_nodes)
    else:
        trajectory_str = f"Unauthorized {incident.get('actionType')} → Autonomous Interception"

    blast_radius = incident.get("blastRadius") or {}
    blast_level = blast_radius.get("blastRadiusLevel", "CRITICAL")
    blast_score = blast_radius.get("blastRadiusScore", 90)

    explanation = {
        "incidentId": incident_id,
        "originalGoal": incident.get("userGoal", "Unknown Goal"),
        "currentAction": f"{incident.get('actionType', 'ACTION')} on '{incident.get('target', 'resource')}'",
        "source": incident.get("source", "AGENT_PLAN"),
        "goalAlignment": f"{incident.get('alignmentScore', 0)}%",
        "trustLevel": incident.get("sourceTrust", "UNTRUSTED"),
        "risk": incident.get("riskLevel", "CRITICAL"),
        "trajectory": trajectory_str,
        "blastRadius": f"{blast_level} ({blast_score}%) — {blast_radius.get('summary', 'High impact')}",
        "decision": "BLOCK",
        "agentState": "FROZEN",
        "triggerReason": incident.get("triggerReason", "Adversarial violation detected."),
        "evidence": incident.get("evidence", [])
    }

    formatted_text = f"""### FORENSIC EXPLANATION — WHY BLOCKED

**Original Goal**: {explanation['originalGoal']}
**Current Action**: {explanation['currentAction']}
**Source**: {explanation['source']}
**Goal Alignment**: {explanation['goalAlignment']}
**Trust**: {explanation['trustLevel']}
**Risk**: {explanation['risk']}
**Trajectory**: {explanation['trajectory']}
**Blast Radius**: {explanation['blastRadius']}
**Decision**: {explanation['decision']}
**Agent State**: {explanation['agentState']}
"""
    explanation["formattedText"] = formatted_text
    return explanation


async def execute_incident_recovery(
    incident_id: str,
    recovery_action: str,
    params: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Executes one of the 5 recovery strategies:
    1. CONTINUE: Unfreeze agent, resume session
    2. ABORT: Safely terminate agent session
    3. ROLLBACK_CHECKPOINT: Restore sandbox files and goal state
    4. EVOLVE_GOAL: Update goal and constraints
    5. START_NEW_SESSION: Reset goal state
    """
    db = get_database()
    params = params or {}
    incident = await get_incident_by_id(incident_id)
    if not incident:
        raise ValueError(f"Incident '{incident_id}' not found.")

    goal_id = incident["goalId"]
    action_clean = recovery_action.strip().upper()
    now_iso = datetime.now(timezone.utc).isoformat()

    result_summary = {}

    if action_clean == "CONTINUE":
        await db.goals.update_one(
            {"goalId": goal_id},
            {"$set": {"status": "ACTIVE", "pauseReason": None, "activeIncidentId": None}}
        )
        result_summary = {"status": "ACTIVE", "message": "Agent unfreezed and execution resumed."}

    elif action_clean == "ABORT":
        await db.goals.update_one(
            {"goalId": goal_id},
            {"$set": {"status": "ABORTED", "pauseReason": "Session aborted by security operator."}}
        )
        result_summary = {"status": "ABORTED", "message": "Agent execution permanently terminated."}

    elif action_clean in ("ROLLBACK_CHECKPOINT", "ROLLBACK"):
        from app.services.checkpoint_service import rollback_to_checkpoint
        checkpoint_id = params.get("checkpointId")
        if not checkpoint_id:
            # Pick latest checkpoint for this goal
            latest_chk = await db.checkpoints.find_one({"goalId": goal_id}, sort=[("createdAt", -1)])
            if not latest_chk:
                raise ValueError("No recovery checkpoint found for this goal.")
            checkpoint_id = latest_chk["checkpointId"]

        rollback_res = await rollback_to_checkpoint(checkpoint_id, goal_id)
        result_summary = {
            "status": "ROLLED_BACK",
            "checkpointId": checkpoint_id,
            "restoredFilesCount": rollback_res.get("restoredFilesCount", 0),
            "message": rollback_res.get("message")
        }

    elif action_clean in ("EVOLVE_GOAL", "MODIFY_GOAL"):
        from app.services.goal_analyzer import GoalAnalyzerService
        evolved_goal = params.get("evolvedGoal") or params.get("userGoal") or incident.get("userGoal")
        evolved_constraints = params.get("evolvedConstraints") or params.get("constraints", [])
        change_reason = params.get("changeReason", "Operator evolved goal policy after security incident.")

        analyzer = GoalAnalyzerService()
        new_policy = await analyzer.analyze_goal(evolved_goal, evolved_constraints)
        
        goal_doc = await db.goals.find_one({"goalId": goal_id})
        new_version = (goal_doc.get("goalVersion", 1) + 1) if goal_doc else 2

        await db.goals.update_one(
            {"goalId": goal_id},
            {
                "$set": {
                    "userGoal": evolved_goal,
                    "constraints": evolved_constraints,
                    "goalPolicy": new_policy,
                    "goalVersion": new_version,
                    "status": "ACTIVE",
                    "pauseReason": None,
                    "activeIncidentId": None
                }
            }
        )
        result_summary = {
            "status": "ACTIVE",
            "goalVersion": new_version,
            "message": f"Goal evolved to V{new_version} and active session resumed."
        }

    elif action_clean in ("START_NEW_SESSION", "RESET"):
        await db.goals.update_one(
            {"goalId": goal_id},
            {"$set": {"status": "IDLE", "pauseReason": None, "activeIncidentId": None}}
        )
        await db.actions.delete_many({"goalId": goal_id})
        result_summary = {"status": "IDLE", "message": "Session reset. Ready for new goal initialization."}

    else:
        raise ValueError(f"Unsupported recovery action: '{recovery_action}'.")

    # Mark incident resolved with recovery notes
    await db.incidents.update_one(
        {"incidentId": incident_id},
        {
            "$set": {
                "status": "RESOLVED",
                "resolution": {
                    "recoveryAction": action_clean,
                    "resolvedAt": now_iso,
                    "details": result_summary
                },
                "updatedAt": now_iso
            }
        }
    )

    return {
        "incidentId": incident_id,
        "goalId": goal_id,
        "recoveryAction": action_clean,
        "result": result_summary,
        "status": "RESOLVED"
    }
