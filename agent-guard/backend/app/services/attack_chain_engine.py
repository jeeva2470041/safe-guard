"""
Attack Chain Graph Engine — Phase 3.

Builds structured directed graph representations of multi-step attack sequences:
- Node: Action / Threat event with metadata (actionId, timestamp, actionType, decision, riskLevel)
- Edge: Temporal sequence & causal link (e.g. prompt injection led to credential read)
- Attack Chain Patterns:
  * CREDENTIAL_THEFT: Prompt Injection -> Goal Hijacking -> Credential Access -> Exfiltration
  * DATA_EXFILTRATION: Sensitive Read -> Encoding -> Outbound Transfer
  * GOAL_HIJACKING: Untrusted Directive -> Domain Drift -> Unauthorized Action
  * DESTRUCTIVE_ATTACK: Command Injection -> Filesystem / Database Wipe
  * MCP_TOOL_POISONING: Poisoned MCP Tool -> Privilege Abuse -> Secret Access
"""

from datetime import datetime, timezone
from typing import Dict, Any, List, Optional


class AttackChainGraph:
    """Represents a detected attack trajectory graph."""

    def __init__(self, attack_type: str, goal_id: str):
        self.attack_type = attack_type
        self.goal_id = goal_id
        self.nodes: List[Dict[str, Any]] = []
        self.edges: List[Dict[str, Any]] = []
        self.evidence: List[str] = []
        self.severity: str = "HIGH"
        self.created_at: str = datetime.now(timezone.utc).isoformat()

    def add_node(self, action_id: str, action_type: str, target: str, decision: str, risk_level: str, role_in_attack: str):
        node = {
            "nodeId": f"node-{len(self.nodes) + 1}",
            "actionId": action_id,
            "actionType": action_type,
            "target": target,
            "decision": decision,
            "riskLevel": risk_level,
            "roleInAttack": role_in_attack,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        self.nodes.append(node)
        if len(self.nodes) > 1:
            prev_node = self.nodes[-2]
            self.edges.append({
                "from": prev_node["nodeId"],
                "to": node["nodeId"],
                "relation": f"escalates_to_{role_in_attack.lower()}"
            })

    def to_dict(self) -> Dict[str, Any]:
        return {
            "attackType": self.attack_type,
            "goalId": self.goal_id,
            "severity": self.severity,
            "nodeCount": len(self.nodes),
            "nodes": self.nodes,
            "edges": self.edges,
            "evidence": self.evidence,
            "createdAt": self.created_at
        }


def evaluate_attack_chain(
    goal_id: str,
    previous_actions: List[Dict[str, Any]],
    current_action: Dict[str, Any],
    prompt_injection_result: Optional[Dict[str, Any]] = None,
    credential_result: Optional[Dict[str, Any]] = None,
    shell_result: Optional[Dict[str, Any]] = None,
    exfil_result: Optional[Dict[str, Any]] = None,
    drift_result: Optional[Dict[str, Any]] = None
) -> Optional[Dict[str, Any]]:
    """
    Evaluates multi-factor signals to construct an Attack Chain Graph if a coherent attack is detected.
    """
    chain = None

    # ── Pattern 1: Credential Theft Chain ──
    # (Prompt injection or untrusted instruction -> Credential Access -> Outbound transfer)
    has_injection = (prompt_injection_result and prompt_injection_result.get("detected")) or any(
        a.get("source") in ("WEBSITE", "DOCUMENT", "EMAIL") and a.get("goalRelationship") == "CONTRADICTORY"
        for a in previous_actions
    )
    has_cred_access = (credential_result and credential_result.get("isCredentialAccess") and not credential_result.get("authorizedByGoal"))
    has_exfil = (exfil_result and exfil_result.get("exfiltrationDetected"))

    if has_cred_access or (has_injection and current_action.get("actionType") in ("SECRET_ACCESS", "FILE_READ", "EXTERNAL_UPLOAD")):
        chain = AttackChainGraph("CREDENTIAL_THEFT", goal_id)
        chain.severity = "CRITICAL"

        if has_injection:
            chain.add_node("EVENT-INJECTION", "PROMPT_INJECTION", "External Web Content", "BLOCK", "CRITICAL", "INJECTION_VECTOR")
            chain.evidence.append("Indirect prompt injection delivered via untrusted content.")

        if drift_result and drift_result.get("isGoalHijacked"):
            chain.add_node("EVENT-HIJACK", "GOAL_HIJACK", "Goal Trajectory", "BLOCK", "HIGH", "OBJECTIVE_MANIPULATION")
            chain.evidence.append(f"Goal trajectory hijacked: {drift_result.get('reason')}")

        if has_cred_access:
            chain.add_node(
                current_action.get("actionId", "ACTION-CURRENT"),
                current_action.get("actionType", "SECRET_ACCESS"),
                current_action.get("target", "credentials"),
                "BLOCK",
                "CRITICAL",
                "CREDENTIAL_EXTRACTION"
            )
            chain.evidence.append(f"Attempted extraction of {credential_result.get('credentialType')}.")

        if has_exfil:
            chain.add_node("EVENT-EXFIL", "DATA_TRANSFER", current_action.get("target", "remote_endpoint"), "BLOCK", "CRITICAL", "EXFILTRATION_SINK")
            chain.evidence.append("Attempted transmission of extracted data to external endpoint.")

        return chain.to_dict()

    # ── Pattern 2: Data Exfiltration Chain ──
    if exfil_result and exfil_result.get("exfiltrationDetected"):
        chain = AttackChainGraph("DATA_EXFILTRATION", goal_id)
        chain.severity = exfil_result.get("severity", "HIGH")
        for link in exfil_result.get("chainLinks", []):
            chain.evidence.append(link)
        chain.add_node(
            current_action.get("actionId", "ACTION-CURRENT"),
            current_action.get("actionType", "EXTERNAL_UPLOAD"),
            current_action.get("target", "external"),
            exfil_result.get("decision", "BLOCK"),
            exfil_result.get("severity", "HIGH"),
            "EXFILTRATION_TRANSFER"
        )
        return chain.to_dict()

    # ── Pattern 3: Destructive Command Attack Chain ──
    if shell_result and shell_result.get("isThreat") and shell_result.get("severity") in ("CRITICAL", "HIGH"):
        chain = AttackChainGraph("DESTRUCTIVE_ATTACK", goal_id)
        chain.severity = shell_result.get("severity", "CRITICAL")
        chain.evidence.append(shell_result.get("reason", "Malicious command execution."))
        chain.add_node(
            current_action.get("actionId", "ACTION-CURRENT"),
            "COMMAND_EXECUTION",
            current_action.get("target", "shell"),
            shell_result.get("decision", "BLOCK"),
            shell_result.get("severity", "CRITICAL"),
            "COMMAND_PAYLOAD"
        )
        return chain.to_dict()

    # ── Pattern 4: Goal Hijacking Chain ──
    if drift_result and drift_result.get("isGoalHijacked") and drift_result.get("driftScore", 0) >= 80:
        chain = AttackChainGraph("GOAL_HIJACKING", goal_id)
        chain.severity = "HIGH"
        chain.evidence.append(drift_result.get("reason", "Goal trajectory hijacked."))
        chain.add_node(
            current_action.get("actionId", "ACTION-CURRENT"),
            current_action.get("actionType", "GENERAL_ACTION"),
            current_action.get("target", "target"),
            "BLOCK",
            "HIGH",
            "DIVERGENT_ACTION"
        )
        return chain.to_dict()

    # ── Pattern 5: Path Traversal / Sandbox Escape Chain ──
    target_str = str(current_action.get("target", "")).lower()
    if ".." in target_str or "/etc" in target_str or "system32" in target_str or "shadow" in target_str or "passwd" in target_str:
        chain = AttackChainGraph("PATH_TRAVERSAL", goal_id)
        chain.severity = "CRITICAL"
        chain.evidence.append("Attempted sandbox escape via directory traversal / sensitive system path.")
        chain.add_node("EVENT-SANDBOX", "SANDBOX_CHECK", "Workspace Boundary", "BLOCK", "HIGH", "CONTAINMENT_TRIGGER")
        chain.add_node(
            current_action.get("actionId", "ACTION-CURRENT"),
            current_action.get("actionType", "FILE_ACCESS"),
            current_action.get("target", "path"),
            "BLOCK",
            "CRITICAL",
            "SANDBOX_ESCAPE"
        )
        return chain.to_dict()

    # ── Pattern 6: Standalone Prompt Injection Chain ──
    if prompt_injection_result and prompt_injection_result.get("detected"):
        chain = AttackChainGraph("PROMPT_INJECTION", goal_id)
        chain.severity = prompt_injection_result.get("severity", "CRITICAL")
        chain.evidence.extend(prompt_injection_result.get("evidence", ["Adversarial prompt injection detected."]))
        chain.add_node("EVENT-INJECTION-SRC", "INJECTION_SOURCE", current_action.get("source", "EXTERNAL"), "BLOCK", "HIGH", "INJECTION_VECTOR")
        chain.add_node(
            current_action.get("actionId", "ACTION-CURRENT"),
            current_action.get("actionType", "EXECUTION_ATTEMPT"),
            current_action.get("target", "target"),
            "BLOCK",
            chain.severity,
            "INJECTED_PAYLOAD"
        )
        return chain.to_dict()

    return None
