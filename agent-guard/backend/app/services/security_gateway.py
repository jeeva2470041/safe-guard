"""
Security Gateway — Dynamic Authorization & Action Execution Engine.

CRITICAL SECURITY MANDATE:
This gateway is the ONLY path to tool execution.
All actions are evaluated dynamically against the user's Goal Policy, Goal Drift,
and Cumulative Risk parameters.
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Any

from app.database.connection import get_database
from app.services.goal_analyzer import GoalAnalyzerService
from app.services.goal_integrity import evaluate_goal_integrity
from app.services.goal_drift import detect_goal_drift
from app.services.risk_engine import evaluate_risk, evaluate_cumulative_risk
from app.services.authorization_engine import make_authorization_decision
from app.services.audit_service import create_audit_log
from app.services.execution_verifier import verify_action_execution
from app.tools.tool_registry import dispatch_tool_execution
from app.tools.file_tools import resolve_sandbox_path

logger = logging.getLogger("agent_guard.security_gateway")


def classify_action(alignment_score: int, risk_level: str, action_type: str, has_violations: bool, target: str) -> str:
    """
    Classify action into standard V5 categories:
    PRODUCTIVE | RELEVANT | UNCERTAIN | UNRELATED | DANGEROUS
    """
    if risk_level == "CRITICAL" or has_violations or ".env" in target.lower() or "delete_database" in action_type.lower():
        return "DANGEROUS"
    if alignment_score >= 80 and risk_level in ("LOW", "MEDIUM"):
        return "PRODUCTIVE"
    if alignment_score >= 60 or action_type in ("READ_FILE", "RUN_TESTS"):
        return "RELEVANT"
    if alignment_score < 40 or risk_level == "HIGH":
        return "UNRELATED"
    return "UNCERTAIN"


async def authorize_and_execute(
    goal_id: str,
    action_type: str,
    target: str,
    description: str,
    agent_id: str = "OPENAI-AGENT-001",
    execute_tool: bool = True
) -> Dict[str, Any]:
    """
    Authorize and optionally execute a proposed action against dynamic Goal Policy.
    """
    db = get_database()

    # Load goal document
    goal = await db.goals.find_one({"goalId": goal_id})
    user_goal = goal["userGoal"] if goal else "Fix login bug"
    constraints = goal.get("constraints", []) if goal else []
    goal_policy = goal.get("goalPolicy") if goal else None
    goal_version = goal.get("goalVersion", 1) if goal else 1

    # If policy is missing, synthesize dynamic policy on the fly
    if not goal_policy:
        analyzer = GoalAnalyzerService()
        goal_policy = await analyzer.analyze_goal(user_goal, constraints)
        if goal:
            await db.goals.update_one({"goalId": goal_id}, {"$set": {"goalPolicy": goal_policy, "goalVersion": goal_version}})

    action_type_clean = action_type.strip().upper()
    target_clean = target.strip()

    # Fetch previous action history for multi-step drift and cumulative risk
    previous_actions = await db.actions.find({"goalId": goal_id}, {"_id": 0}).to_list(length=100)

    # ── Step 1: Sandbox & Workspace Path Traversal Check ──
    is_path_traversal = False
    # Check for relative path traversal escape (e.g. ../../etc/passwd)
    norm_path_parts = target_clean.replace("\\", "/").split("/")
    if ".." in norm_path_parts:
        is_path_traversal = True
        logger.warning(f"Path traversal escape blocked: {target_clean}")
    elif execute_tool and agent_id not in ("GOOGLE-ANTIGRAVITY", "antigravity"):
        try:
            if action_type_clean not in ("RUN_TESTS", "RUN_COMMAND", "EXTERNAL_UPLOAD", "ACCESS_ENV", "COMPLETE"):
                resolve_sandbox_path(target_clean)
        except ValueError as err:
            is_path_traversal = True
            logger.warning(f"Sandbox path traversal blocked: {err}")

    if is_path_traversal:
        integrity = {
            "goalAlignmentScore": 0,
            "alignmentStatus": "UNALIGNED",
            "violatedConstraints": ["Sandbox Boundary Constraint"],
            "reason": "Target is outside the permitted sandbox directory."
        }
        drift = {
            "driftScore": 100,
            "driftLevel": "CRITICAL",
            "driftDetected": True,
            "rollingIntegrity": 0.0,
            "reason": "Path traversal moves completely outside project scope."
        }
        risk = {
            "riskLevel": "CRITICAL",
            "riskScore": 100,
            "riskReason": "Attempted path traversal outside permitted sandbox boundary."
        }
        cumulative_risk = {
            "cumulativeRiskScore": 100,
            "cumulativeRiskLevel": "CRITICAL",
            "cumulativeRiskReason": "Severe security violation: Sandbox escape attempt."
        }
        auth = {
            "decision": "BLOCK",
            "reason": "Action blocked: Target is outside the permitted sandbox directory."
        }
    else:
        # ── Step 2: Dynamic Goal Integrity Check ──
        integrity = evaluate_goal_integrity(
            user_goal=user_goal,
            action_type=action_type_clean,
            target=target_clean,
            description=description,
            constraints=constraints,
            goal_policy=goal_policy
        )

        # ── Step 3: Multi-Step Goal Drift Detection ──
        drift = detect_goal_drift(
            goal_policy=goal_policy,
            previous_actions=previous_actions,
            proposed_action={
                "actionType": action_type_clean,
                "target": target_clean,
                "description": description
            }
        )

        # ── Step 4: Contextual & Cumulative Risk Assessment ──
        risk = evaluate_risk(action_type_clean, target_clean)
        cumulative_risk = evaluate_cumulative_risk(previous_actions, risk)

        # ── Step 5: Authorization Decision Matrix ──
        auth = make_authorization_decision(
            alignment_status=integrity["alignmentStatus"],
            alignment_score=integrity["goalAlignmentScore"],
            risk_level=risk["riskLevel"],
            risk_score=risk["riskScore"],
            alignment_reason=integrity["reason"],
            risk_reason=risk["riskReason"],
        )

        # ── Step 6: Dynamic Rule Overrides ──
        # If explicit constraints violated or severe drift detected → BLOCK
        if integrity["violatedConstraints"] or drift["driftScore"] >= 75:
            auth["decision"] = "BLOCK"
            violated_str = ", ".join(integrity["violatedConstraints"]) if integrity["violatedConstraints"] else drift["reason"]
            auth["reason"] = f"Action BLOCKED: {violated_str}"

    decision = auth["decision"]

    # ── Step 7: Automatic Agent Pausing Check ──
    should_pause_agent = (
        drift["driftLevel"] == "CRITICAL"
        or cumulative_risk["cumulativeRiskLevel"] == "CRITICAL"
        or bool(integrity["violatedConstraints"])
        or risk["riskLevel"] == "CRITICAL"
    )

    pause_triggered = False
    pause_reason = ""
    if should_pause_agent and action_type_clean != "COMPLETE":
        pause_triggered = True
        pause_reason = (
            f"Automatic Security Pause: {drift['reason']} "
            f"Cumulative Risk: {cumulative_risk['cumulativeRiskLevel']} ({cumulative_risk['cumulativeRiskScore']}%)."
        )
        # Update Goal Status to PAUSED in MongoDB
        if goal:
            await db.goals.update_one(
                {"goalId": goal_id},
                {
                    "$set": {
                        "status": "PAUSED",
                        "pauseReason": pause_reason,
                        "pausedAt": datetime.now(timezone.utc).isoformat(),
                        "recentDivergentAction": f"{action_type_clean} on {target_clean}"
                    }
                }
            )

    # Action classification
    action_class = classify_action(
        alignment_score=integrity["goalAlignmentScore"],
        risk_level=risk["riskLevel"],
        action_type=action_type_clean,
        has_violations=bool(integrity["violatedConstraints"]),
        target=target_clean
    )

    # Map execution status
    if decision == "ALLOW":
        execution_status = "EXECUTED"
    elif decision == "REQUIRE_APPROVAL":
        execution_status = "PENDING_APPROVAL"
    else:  # BLOCK
        execution_status = "NOT_EXECUTED"

    # ── Step 8: Controlled Tool Execution (ONLY if ALLOW and execute_tool is True) ──
    tool_output = None
    if decision == "ALLOW":
        if execute_tool:
            try:
                tool_output = dispatch_tool_execution(action_type_clean, target_clean, description)
            except Exception as ex:
                logger.error(f"Tool execution failed: {ex}")
                execution_status = "FAILED"
                tool_output = {"status": "error", "message": str(ex)}
        else:
            # Delegated to external agent (e.g. Antigravity)
            tool_output = {"status": "delegated", "message": "Authorized for execution by Antigravity runtime."}

    # ── Step 9: Post-Execution Verification ──
    if execute_tool:
        verification = verify_action_execution(
            action_type=action_type_clean,
            target=target_clean,
            decision=decision,
            execution_status=execution_status
        )
    else:
        verification = {
            "verificationStatus": "PASSED" if decision == "ALLOW" else ("PENDING" if decision == "REQUIRE_APPROVAL" else "BLOCKED"),
            "verificationMessage": f"PreToolUse Interception: Gateway decision '{decision}' enforced before tool execution."
        }

    # ── Step 10: MongoDB Persistence ──
    count = await db.actions.count_documents({"goalId": goal_id})
    action_id = f"{goal_id}-A-{count + 1:03d}"
    now_iso = datetime.now(timezone.utc).isoformat()

    scope_violation = (
        bool(integrity["violatedConstraints"])
        or drift["driftScore"] >= 50
        or integrity["alignmentStatus"] == "UNALIGNED"
    )

    action_doc = {
        "actionId": action_id,
        "goalId": goal_id,
        "goalVersion": goal_version,
        "agentId": agent_id,
        "actionType": action_type_clean,
        "target": target_clean,
        "description": description,
        "goalAlignmentScore": integrity["goalAlignmentScore"],
        "alignmentScore": integrity["goalAlignmentScore"],
        "alignmentStatus": integrity["alignmentStatus"],
        "driftScore": drift["driftScore"],
        "driftLevel": drift.get("driftLevel", "NORMAL"),
        "driftDetected": drift["driftDetected"],
        "rollingIntegrity": drift.get("rollingIntegrity", 100.0),
        "violatedConstraints": integrity["violatedConstraints"],
        "scopeViolation": scope_violation,
        "riskLevel": risk["riskLevel"],
        "riskScore": risk["riskScore"],
        "cumulativeRiskScore": cumulative_risk["cumulativeRiskScore"],
        "cumulativeRiskLevel": cumulative_risk["cumulativeRiskLevel"],
        "actionClassification": action_class,
        "decision": decision,
        "reason": auth["reason"],
        "executionStatus": execution_status,
        "verificationStatus": verification["verificationStatus"],
        "verificationMessage": verification["verificationMessage"],
        "pauseTriggered": pause_triggered,
        "pauseReason": pause_reason,
        "toolOutput": tool_output,
        "createdAt": now_iso,
        "timestamp": now_iso,
    }

    await db.actions.insert_one(action_doc)

    await create_audit_log(
        goal_id=goal_id,
        action_id=action_id,
        decision=decision,
        risk_level=risk["riskLevel"],
        reason=auth["reason"],
    )

    return action_doc
