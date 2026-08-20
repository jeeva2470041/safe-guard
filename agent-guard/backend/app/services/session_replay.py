"""
Session Replay Service — Phase 4.

Generates chronological step-by-step interactive replay sequences:
USER GOAL -> ACTION 1 -> ACTION 2 -> ACTION 3 -> ATTACK -> BLOCK

Enables security operators to scrub, inspect, and evaluate multi-step trajectories.
"""

from typing import Dict, Any, List
from app.database.connection import get_database
from app.services.blast_radius_engine import calculate_blast_radius


async def generate_session_replay(goal_id: str) -> Dict[str, Any]:
    """
    Generates a structured chronological replay timeline for a monitored agent session.
    """
    db = get_database()
    goal = await db.goals.find_one({"goalId": goal_id})
    user_goal = goal["userGoal"] if goal else "Perform requested task"
    constraints = goal.get("constraints", []) if goal else []
    goal_status = goal.get("status", "ACTIVE") if goal else "ACTIVE"

    actions = await db.actions.find({"goalId": goal_id}, {"_id": 0}).sort("timestamp", 1).to_list(length=200)
    incidents = await db.incidents.find({"goalId": goal_id}, {"_id": 0}).to_list(length=50)

    steps = []

    # Step 0: Goal Initialization
    steps.append({
        "stepIndex": 0,
        "stepType": "GOAL_INITIALIZATION",
        "title": "Goal Initialization & Intent Formulation",
        "userGoal": user_goal,
        "constraints": constraints,
        "timestamp": goal.get("createdAt") if goal else None,
        "decision": "INITIALIZED",
        "goalAlignmentScore": 100,
        "driftScore": 0,
        "riskLevel": "LOW",
        "description": f"User established active goal: '{user_goal}'.",
        "isAttackEvent": False
    })

    attack_detected = False

    for idx, act in enumerate(actions, start=1):
        decision = act.get("decision", "ALLOW")
        is_attack = decision == "BLOCK" or act.get("riskLevel") == "CRITICAL" or act.get("isGoalHijacked", False)
        if is_attack:
            attack_detected = True

        # Calculate or load blast radius
        blast_radius = act.get("blastRadius")
        if not blast_radius:
            blast_radius = calculate_blast_radius(
                action_type=act.get("actionType", "UNKNOWN"),
                target=act.get("target", "N/A"),
                description=act.get("description", ""),
                user_goal=user_goal
            )

        step_type = "ATTACK_INTERCEPTION" if is_attack else "TOOL_ACTION"
        title = f"Step {idx}: {act.get('actionType', 'ACTION')} — {act.get('target', '')}"

        steps.append({
            "stepIndex": idx,
            "stepType": step_type,
            "title": title,
            "actionId": act.get("actionId"),
            "actionType": act.get("actionType"),
            "target": act.get("target"),
            "description": act.get("description"),
            "source": act.get("source", "AGENT_PLAN"),
            "goalRelationship": act.get("goalRelationship", "SUPPORTING"),
            "sourceTrustLevel": act.get("sourceTrustLevel", "TRUSTED"),
            "goalAlignmentScore": act.get("goalAlignmentScore", 100),
            "driftScore": act.get("driftScore", 0),
            "riskLevel": act.get("riskLevel", "LOW"),
            "blastRadius": blast_radius,
            "decision": decision,
            "reason": act.get("reason", ""),
            "executionStatus": act.get("executionStatus", "EXECUTED"),
            "toolOutput": act.get("toolOutput"),
            "isAttackEvent": is_attack,
            "timestamp": act.get("timestamp")
        })

    # Terminal Step: Final Containment Summary
    total_actions = len(actions)
    blocked_count = sum(1 for a in actions if a.get("decision") == "BLOCK")

    steps.append({
        "stepIndex": len(steps),
        "stepType": "SESSION_SUMMARY",
        "title": "Session Governance Summary",
        "goalStatus": goal_status,
        "totalActions": total_actions,
        "blockedCount": blocked_count,
        "incidentsRecorded": len(incidents),
        "attackDetected": attack_detected,
        "description": f"Session concluded with status '{goal_status}'. {blocked_count} blocked actions out of {total_actions} total proposed.",
        "isAttackEvent": False
    })

    return {
        "goalId": goal_id,
        "userGoal": user_goal,
        "goalStatus": goal_status,
        "totalSteps": len(steps),
        "steps": steps,
        "attackDetected": attack_detected,
        "incidentCount": len(incidents)
    }
