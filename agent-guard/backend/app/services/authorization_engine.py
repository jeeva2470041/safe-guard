"""
Authorization Engine — Multi-Factor Deterministic Decision Matrix.

Integrates:
- Goal Alignment (Relationship: DIRECTLY_RELEVANT | SUPPORTING | INDIRECTLY_RELEVANT | UNRELATED | CONTRADICTORY)
- Instruction Source Trust (USER | AGENT_PLAN | WEBSITE | DOCUMENT | EMAIL | SEARCH_RESULT | UNKNOWN)
- Authority Scope (Financial, Communication, Personal Data)
- Contextual Risk & Consequence Levels (LOW | MEDIUM | HIGH | CRITICAL)
- Multi-Step Trajectory Drift
- Session Whitelists (APPROVE_SIMILAR history)

Formula:
  Goal Alignment + Source Trust + Authority Scope + Risk + Consequence + Trajectory Drift
  -> ALLOW | REQUIRE_APPROVAL | BLOCK
"""

from typing import Dict, Any, List, Optional

# Decision matrix: alignment_status × risk_level → base decision
DECISION_MATRIX = {
    ("ALIGNED", "LOW"): "ALLOW",
    ("ALIGNED", "MEDIUM"): "ALLOW",
    ("ALIGNED", "HIGH"): "REQUIRE_APPROVAL",
    ("ALIGNED", "CRITICAL"): "BLOCK",

    ("PARTIALLY_ALIGNED", "LOW"): "ALLOW",
    ("PARTIALLY_ALIGNED", "MEDIUM"): "REQUIRE_APPROVAL",
    ("PARTIALLY_ALIGNED", "HIGH"): "REQUIRE_APPROVAL",
    ("PARTIALLY_ALIGNED", "CRITICAL"): "BLOCK",

    ("UNALIGNED", "LOW"): "ALLOW",
    ("UNALIGNED", "MEDIUM"): "BLOCK",
    ("UNALIGNED", "HIGH"): "BLOCK",
    ("UNALIGNED", "CRITICAL"): "BLOCK",
}

DECISION_REASONS = {
    "ALLOW": "Action is aligned with the user's intent, authorized by policy, and poses acceptable risk.",
    "REQUIRE_APPROVAL": "Action requires human review due to financial impact, external communication, or elevated consequence.",
    "BLOCK": "Action is blocked due to misalignment, untrusted source instruction, constraint violation, or critical risk.",
}


def is_action_covered_by_similar_approval(action_type: str, target: str, approved_similar_actions: List[Dict[str, Any]]) -> bool:
    """Check if the action matches a previously approved similar action pattern in the active session."""
    if not approved_similar_actions:
        return False

    action_upper = action_type.upper()
    target_lower = target.lower()

    for pattern in approved_similar_actions:
        p_type = str(pattern.get("actionType", "")).upper()
        p_target = str(pattern.get("target", "")).lower()

        if p_type == action_upper:
            # If target matches or is sub-path/domain of pattern target
            if not p_target or p_target in target_lower or target_lower in p_target:
                return True

    return False


def make_authorization_decision(
    alignment_status: str,
    alignment_score: int,
    risk_level: str,
    risk_score: int,
    alignment_reason: str,
    risk_reason: str,
    goal_relationship: str = "SUPPORTING",
    source_trust_level: str = "TRUSTED",
    consequence: Optional[str] = None,
    consequence_level: str = "LOW",
    reversibility: str = "REVERSIBLE",
    financial_authority: Optional[Dict[str, Any]] = None,
    communication_authority: Optional[Dict[str, Any]] = None,
    action_type: str = "GENERAL_ACTION",
    target: str = "",
    approved_similar_actions: Optional[List[Dict[str, Any]]] = None,
    is_aborted: bool = False
) -> dict:
    """
    Make a multi-factor deterministic authorization decision.
    """
    if is_aborted:
        return {
            "decision": "BLOCK",
            "reason": "Session has been aborted by the user. No further actions are permitted.",
            "goalRelationship": "CONTRADICTORY",
            "sourceTrustLevel": source_trust_level,
            "reversibility": reversibility,
            "consequenceLevel": consequence_level
        }

    action_upper = action_type.upper()
    key = (alignment_status, risk_level)
    decision = DECISION_MATRIX.get(key, "BLOCK")

    # 1. Check Session Whitelist (APPROVE_SIMILAR)
    if approved_similar_actions and is_action_covered_by_similar_approval(action_upper, target, approved_similar_actions):
        if risk_level != "CRITICAL" and goal_relationship != "CONTRADICTORY":
            decision = "ALLOW"

    # 2. Contradictory Goal Relationship or Untrusted Source Injection -> Hard BLOCK
    elif goal_relationship == "CONTRADICTORY" or (source_trust_level == "UNTRUSTED" and risk_level in ("HIGH", "CRITICAL")):
        decision = "BLOCK"

    # 3. Critical Risk Target -> Hard BLOCK
    elif risk_level == "CRITICAL" or consequence_level == "CRITICAL":
        decision = "BLOCK"

    # 4. Financial Payment Actions
    elif action_upper in ("EXTERNAL_TRANSACTION", "FINANCIAL_INITIATE_PAYMENT", "FINANCIAL_CONFIRM_PAYMENT", "PAYMENT") or "pay" in action_upper.lower():
        if financial_authority and financial_authority.get("authorized", False) and not financial_authority.get("requiresApproval", True):
            decision = "ALLOW"
        else:
            decision = "REQUIRE_APPROVAL"

    # 5. External Communication Actions
    elif action_upper in ("EXTERNAL_COMMUNICATION", "EMAIL_SEND", "SEND_EMAIL") or ("email" in action_upper.lower() and "send" in action_upper.lower()):
        if communication_authority and communication_authority.get("authorized", False) and not communication_authority.get("requiresApproval", True):
            decision = "ALLOW"
        else:
            decision = "REQUIRE_APPROVAL"

    # 6. Direct / Supporting Safe Actions (Flight searches, Room picks, Form filling, Component edits)
    elif goal_relationship in ("DIRECTLY_RELEVANT", "SUPPORTING") and risk_level in ("LOW", "MEDIUM"):
        decision = "ALLOW"

    # Human-readable explanation
    base_reason = DECISION_REASONS.get(decision, "Evaluated action against security policy.")
    detailed_parts = [base_reason]
    detailed_parts.append(f"Intent Alignment: {alignment_score}% ({alignment_status}, {goal_relationship}).")
    detailed_parts.append(f"Risk Rating: {risk_level} (score: {risk_score}, consequence: {consequence_level}).")

    if consequence:
        detailed_parts.append(f"Impact: {consequence}")
    if decision == "BLOCK":
        detailed_parts.append(f"Violation: {alignment_reason}")
    elif decision == "REQUIRE_APPROVAL":
        detailed_parts.append(f"Confirmation required: {alignment_reason or risk_reason}")

    detailed_reason = " ".join(detailed_parts)

    return {
        "decision": decision,
        "reason": detailed_reason,
        "goalRelationship": goal_relationship,
        "sourceTrustLevel": source_trust_level,
        "reversibility": reversibility,
        "consequenceLevel": consequence_level
    }
