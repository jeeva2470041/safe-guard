"""
Security Gateway — Dynamic Authorization & Action Execution Engine.

CRITICAL SECURITY MANDATE:
This gateway is the ONLY path to tool execution.
All actions are evaluated dynamically against the user's User Intent Model,
Instruction Source Trust, Sub-Goal hierarchy, and Multi-Step Drift/Risk parameters.

Phase 1: Intent-Preserving Policy Foundation
Phase 2: Real-World Action Authorization & External Trust Gateway
Phase 3: Runtime Attack-Detection & Containment System (Prompt Injection, Hijacking, Credentials, Exfiltration, Shell, MCP, Filesystem, Incidents)
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional

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

# Phase 3 Attack Detection Services
from app.services.prompt_injection_detector import detect_prompt_injection
from app.services.credential_guard import check_credential_access
from app.services.shell_security import inspect_command_security
from app.services.filesystem_guard import validate_filesystem_path
from app.services.mcp_security import inspect_mcp_invocation
from app.services.exfiltration_detector import detect_exfiltration_chain
from app.services.attack_chain_engine import evaluate_attack_chain
from app.services.incident_manager import create_security_incident

logger = logging.getLogger("agent_guard.security_gateway")


def classify_action(alignment_score: int, risk_level: str, action_type: str, has_violations: bool, target: str) -> str:
    """
    Classify action into standard categories:
    PRODUCTIVE | RELEVANT | UNCERTAIN | UNRELATED | DANGEROUS
    """
    if risk_level == "CRITICAL" or has_violations or ".env" in target.lower() or "id_rsa" in target.lower() or "delete_database" in action_type.lower():
        return "DANGEROUS"
    if alignment_score >= 75 and risk_level in ("LOW", "MEDIUM"):
        return "PRODUCTIVE"
    if alignment_score >= 50 or action_type in ("READ_FILE", "FILE_READ", "RUN_TESTS", "BROWSER_SEARCH", "BROWSER_NAVIGATE", "API_GET"):
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
    execute_tool: bool = True,
    source: str = "AGENT_PLAN",
    purpose: Optional[str] = None,
    consequence: Optional[str] = None,
    consequence_level: str = "LOW",
    reversibility: str = "REVERSIBLE"
) -> Dict[str, Any]:
    """
    Authorize and optionally execute a proposed action against dynamic User Intent Model & Phase 3 Attack Detection.
    """
    db = get_database()

    # Load goal document
    goal = await db.goals.find_one({"goalId": goal_id})
    user_goal = goal["userGoal"] if goal else "Perform requested task"
    constraints = goal.get("constraints", []) if goal else []
    goal_policy = goal.get("goalPolicy") if goal else None
    goal_version = goal.get("goalVersion", 1) if goal else 1
    approved_similar = goal.get("approvedSimilarActions", []) if goal else []
    is_aborted = (goal.get("status") == "ABORTED") if goal else False

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

    # ── Step 1: Sandbox & Workspace Path Traversal Check (For File Tools) ──
    fs_check = validate_filesystem_path(target_clean)
    is_path_traversal = not fs_check["isValid"]

    if not is_path_traversal and execute_tool and agent_id not in ("GOOGLE-ANTIGRAVITY", "antigravity"):
        try:
            if action_type_clean in ("READ_FILE", "WRITE_FILE", "MODIFY_FILE", "DELETE_FILE", "FILE_READ", "FILE_WRITE", "FILE_DELETE"):
                resolve_sandbox_path(target_clean)
        except ValueError as err:
            is_path_traversal = True
            logger.warning(f"Sandbox path traversal blocked: {err}")

    if is_path_traversal:
        integrity = {
            "goalAlignmentScore": 0,
            "alignmentScore": 0,
            "alignmentStatus": "UNALIGNED",
            "violatedConstraints": ["Sandbox Boundary Constraint", "Path Traversal Violation"],
            "reason": fs_check.get("reason") or "Target is outside the permitted sandbox directory.",
            "goalRelationship": "CONTRADICTORY",
            "goal_relationship": "CONTRADICTORY",
            "requiredForGoal": False,
            "required_for_goal": False,
            "currentSubGoal": None,
            "current_sub_goal": None,
            "sourceTrustLevel": "UNTRUSTED"
        }
        drift = {
            "driftScore": 100,
            "driftLevel": "CRITICAL",
            "driftDetected": True,
            "isGoalHijacked": True,
            "hijackingConfidence": 1.0,
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
            "reason": "Action blocked: Target is outside the permitted sandbox directory.",
            "goalRelationship": "CONTRADICTORY",
            "sourceTrustLevel": "UNTRUSTED",
            "reversibility": "IRREVERSIBLE",
            "consequenceLevel": "CRITICAL"
        }
        attack_chain = evaluate_attack_chain(
            goal_id=goal_id,
            previous_actions=previous_actions,
            current_action={
                "actionId": f"{goal_id}-A-PROPOSED",
                "actionType": action_type_clean,
                "target": target_clean,
                "description": description
            },
            drift_result=drift
        )
    else:
        # ── Step 2: Dynamic Goal Integrity & Intent Evaluation ──
        integrity = evaluate_goal_integrity(
            user_goal=user_goal,
            action_type=action_type_clean,
            target=target_clean,
            description=description,
            constraints=constraints,
            goal_policy=goal_policy,
            source=source,
            purpose=purpose,
            previous_actions=previous_actions
        )

        # ── Step 3: Multi-Step Goal Drift & Hijacking Detection ──
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
        from app.services.action_normalizer import determine_action_consequence_and_reversibility
        calc_desc, calc_level, calc_rev = determine_action_consequence_and_reversibility(action_type_clean, target_clean, {})
        consequence = consequence or calc_desc
        if not consequence_level or consequence_level == "LOW":
            consequence_level = calc_level
        if not reversibility or reversibility == "REVERSIBLE":
            reversibility = calc_rev

        risk = evaluate_risk(action_type_clean, target_clean)
        cumulative_risk = evaluate_cumulative_risk(previous_actions, risk)

        # ── Step 5 (Phase 3): Multi-Factor Attack Detection Pipeline ──
        prompt_injection_res = detect_prompt_injection(
            content=f"{description} {target_clean}",
            user_goal=user_goal,
            source=source,
            action_type=action_type_clean,
            target=target_clean
        )

        cred_guard_res = check_credential_access(
            action_type=action_type_clean,
            target=target_clean,
            description=description,
            user_goal=user_goal,
            source=source
        )

        shell_res = None
        if action_type_clean in ("COMMAND_EXECUTION", "RUN_COMMAND"):
            shell_res = inspect_command_security(target_clean, user_goal)

        mcp_res = None
        if action_type_clean.startswith("MCP_") or "mcp" in action_type_clean.lower():
            mcp_res = inspect_mcp_invocation(target_clean, {}, user_goal)

        exfil_res = detect_exfiltration_chain(
            previous_actions=previous_actions,
            current_action={
                "actionType": action_type_clean,
                "target": target_clean,
                "description": description
            },
            user_goal=user_goal
        )

        attack_chain = evaluate_attack_chain(
            goal_id=goal_id,
            previous_actions=previous_actions,
            current_action={
                "actionId": f"{goal_id}-A-PROPOSED",
                "actionType": action_type_clean,
                "target": target_clean,
                "description": description
            },
            prompt_injection_result=prompt_injection_res,
            credential_result=cred_guard_res,
            shell_result=shell_res,
            exfil_result=exfil_res,
            drift_result=drift
        )

        # ── Step 6: Authorization Decision Matrix ──
        auth = make_authorization_decision(
            alignment_status=integrity["alignmentStatus"],
            alignment_score=integrity["goalAlignmentScore"],
            risk_level=risk["riskLevel"],
            risk_score=risk["riskScore"],
            alignment_reason=integrity["reason"],
            risk_reason=risk["riskReason"],
            goal_relationship=integrity.get("goalRelationship", "SUPPORTING"),
            source_trust_level=integrity.get("sourceTrustLevel", "TRUSTED"),
            consequence=consequence,
            consequence_level=consequence_level,
            reversibility=reversibility,
            financial_authority=goal_policy.get("financial_authority") if goal_policy else None,
            communication_authority=goal_policy.get("external_communication_authority") if goal_policy else None,
            action_type=action_type_clean,
            target=target_clean,
            approved_similar_actions=approved_similar,
            is_aborted=is_aborted
        )

        # ── Step 7: Phase 3 Attack Containment & Rule Overrides ──
        detected_attacks = []
        if cred_guard_res["isCredentialAccess"] and not cred_guard_res["authorizedByGoal"]:
            detected_attacks.append(f"Unauthorized Credential Access: {cred_guard_res['reason']}")
            auth["decision"] = "BLOCK"
            risk["riskLevel"] = "CRITICAL"
            consequence_level = "CRITICAL"

        if prompt_injection_res["detected"] and prompt_injection_res["severity"] in ("CRITICAL", "HIGH"):
            detected_attacks.append(f"Prompt Injection Attack: {prompt_injection_res['recommendation']}")
            auth["decision"] = "BLOCK"
            risk["riskLevel"] = "CRITICAL"

        if shell_res and shell_res["isThreat"] and shell_res["severity"] in ("CRITICAL", "HIGH"):
            detected_attacks.append(f"Malicious Shell Command: {shell_res['reason']}")
            auth["decision"] = "BLOCK"
            risk["riskLevel"] = "CRITICAL"

        if exfil_res and exfil_res["exfiltrationDetected"]:
            detected_attacks.append(f"Data Exfiltration Chain: {exfil_res['reason']}")
            auth["decision"] = "BLOCK"
            risk["riskLevel"] = "CRITICAL"

        if mcp_res and mcp_res["isThreat"]:
            detected_attacks.append(f"Poisoned MCP Tool Invocation: {mcp_res['reason']}")
            auth["decision"] = "BLOCK"
            risk["riskLevel"] = "CRITICAL"

        if drift.get("isGoalHijacked") and drift["driftScore"] >= 80:
            detected_attacks.append(f"Goal Hijacking Detected: {drift['reason']}")
            auth["decision"] = "BLOCK"
            risk["riskLevel"] = "CRITICAL"

        if integrity["violatedConstraints"] or drift["driftScore"] >= 75 or integrity.get("goalRelationship") == "CONTRADICTORY":
            auth["decision"] = "BLOCK"
            violated_str = ", ".join(integrity["violatedConstraints"]) if integrity["violatedConstraints"] else drift["reason"]
            auth["reason"] = f"Action BLOCKED: {violated_str}"

        # If attack was detected, update reason and trigger incident creation
        if detected_attacks:
            auth["reason"] = f"Action BLOCKED by Phase 3 Attack Containment: {'; '.join(detected_attacks)}"

    decision = auth["decision"]

    # ── Step 8: Automatic Incident Creation & Agent Pausing Check ──
    should_create_incident = (
        decision == "BLOCK" and (
            risk["riskLevel"] == "CRITICAL"
            or drift.get("isGoalHijacked", False)
            or is_path_traversal
            or (prompt_injection_res["detected"] if 'prompt_injection_res' in locals() else False)
            or (cred_guard_res["isCredentialAccess"] and not cred_guard_res["authorizedByGoal"] if 'cred_guard_res' in locals() else False)
            or (shell_res and shell_res["isThreat"] if 'shell_res' in locals() else False)
        )
    )

    should_pause_agent = (
        drift["driftLevel"] == "CRITICAL"
        or cumulative_risk["cumulativeRiskLevel"] == "CRITICAL"
        or bool(integrity["violatedConstraints"])
        or risk["riskLevel"] == "CRITICAL"
        or integrity.get("goalRelationship") == "CONTRADICTORY"
        or should_create_incident
    )

    pause_triggered = False
    pause_reason = ""
    if should_pause_agent and action_type_clean != "COMPLETE" and not is_aborted:
        pause_triggered = True
        pause_reason = (
            f"Security Containment Activated: {auth['reason']} "
            f"Cumulative Risk: {cumulative_risk['cumulativeRiskLevel']} ({cumulative_risk['cumulativeRiskScore']}%)."
        )
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

    # If critical incident detected, record to 'incidents' collection
    if should_create_incident:
        await create_security_incident(
            goal_id=goal_id,
            attack_type=attack_chain["attackType"] if ('attack_chain' in locals() and attack_chain) else "CRITICAL_SECURITY_VIOLATION",
            severity="CRITICAL",
            action_id=f"{goal_id}-A-INCIDENT",
            action_type=action_type_clean,
            target=target_clean,
            evidence=attack_chain.get("evidence", [auth["reason"]]) if ('attack_chain' in locals() and attack_chain) else [auth["reason"]],
            attack_chain=attack_chain if 'attack_chain' in locals() else None,
            trigger_reason=auth["reason"]
        )

    action_class = classify_action(
        alignment_score=integrity["goalAlignmentScore"],
        risk_level=risk["riskLevel"],
        action_type=action_type_clean,
        has_violations=bool(integrity["violatedConstraints"]),
        target=target_clean
    )

    if decision == "ALLOW":
        execution_status = "EXECUTED"
    elif decision == "REQUIRE_APPROVAL":
        execution_status = "PENDING_APPROVAL"
    else:  # BLOCK
        execution_status = "NOT_EXECUTED"

    # ── Step 9: Controlled Tool Execution ──
    tool_output = None
    if decision == "ALLOW":
        if execute_tool:
            try:
                tool_output = dispatch_tool_execution(action_type_clean, target_clean, description)
            except Exception as ex:
                logger.error(f"Tool execution failed: {ex}")
                execution_status = "FAILED"
                tool_output = str(ex)

    # ── Step 10: Post-Execution Verification ──
    verification = verify_action_execution(
        action_type=action_type_clean,
        target=target_clean,
        decision=decision,
        execution_status=execution_status
    )

    # ── Step 11: Generate Action Count for ID ──
    action_count = await db.actions.count_documents({"goalId": goal_id})
    action_id = f"{goal_id}-A-{str(action_count + 1).zfill(3)}"

    action_doc = {
        "actionId": action_id,
        "goalId": goal_id,
        "goalVersion": goal_version,
        "agentId": agent_id,
        "actionType": action_type_clean,
        "description": description,
        "target": target_clean,

        # Phase 1, 2 & 3 Forensics
        "source": source,
        "purpose": purpose or description,
        "goalRelationship": integrity.get("goalRelationship", "SUPPORTING"),
        "goal_relationship": integrity.get("goalRelationship", "SUPPORTING"),
        "requiredForGoal": integrity.get("requiredForGoal", True),
        "required_for_goal": integrity.get("requiredForGoal", True),
        "consequence": consequence or risk.get("riskReason"),
        "consequenceLevel": consequence_level or "LOW",
        "reversibility": reversibility,
        "currentSubGoal": integrity.get("currentSubGoal"),
        "current_sub_goal": integrity.get("currentSubGoal"),
        "sourceTrustLevel": integrity.get("sourceTrustLevel", "TRUSTED"),

        "goalAlignmentScore": integrity["goalAlignmentScore"],
        "alignmentScore": integrity["goalAlignmentScore"],
        "alignmentStatus": integrity["alignmentStatus"],
        "driftScore": drift["driftScore"],
        "driftLevel": drift["driftLevel"],
        "driftDetected": drift["driftDetected"],
        "isGoalHijacked": drift.get("isGoalHijacked", False),
        "rollingIntegrity": drift["rollingIntegrity"],
        "violatedConstraints": integrity["violatedConstraints"],
        "scopeViolation": bool(integrity["violatedConstraints"]),
        "riskLevel": risk["riskLevel"],
        "riskScore": risk["riskScore"],
        "cumulativeRiskScore": cumulative_risk["cumulativeRiskScore"],
        "cumulativeRiskLevel": cumulative_risk["cumulativeRiskLevel"],
        "actionClassification": action_class,
        "decision": decision,
        "reason": auth["reason"],
        "executionStatus": execution_status,
        "toolOutput": tool_output,
        "verificationStatus": verification["verificationStatus"],
        "verificationMessage": verification["verificationMessage"],
        "pauseTriggered": pause_triggered,
        "pauseReason": pause_reason,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    # Save action document to MongoDB
    await db.actions.insert_one(action_doc)

    # Log to tamper-evident audit collection
    await create_audit_log(
        goal_id=goal_id,
        action_id=action_id,
        decision=decision,
        risk_level=risk["riskLevel"],
        reason=auth["reason"]
    )

    action_doc.pop("_id", None)
    return action_doc
