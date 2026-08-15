"""
Authorization Engine — Combines goal integrity and risk assessment
to make an authorization decision.

Decision Matrix:
              | LOW Risk     | MEDIUM Risk       | HIGH Risk    | CRITICAL Risk
ALIGNED       | ALLOW        | ALLOW             | REQ_APPROVAL | BLOCK
PARTIAL       | ALLOW        | REQUIRE_APPROVAL  | BLOCK        | BLOCK
UNALIGNED     | REQ_APPROVAL | BLOCK             | BLOCK        | BLOCK

Returns:
    decision: ALLOW | REQUIRE_APPROVAL | BLOCKED
    reason: explanation string
"""

# Decision matrix: alignment_status × risk_level → decision
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

# Human-readable reasons for each decision
DECISION_REASONS = {
    "ALLOW": "Action is aligned with the user's goal and poses acceptable risk. Approved for execution.",
    "REQUIRE_APPROVAL": "Action requires human review due to partial alignment or elevated risk level.",
    "BLOCK": "Action is blocked due to misalignment with user's goal and/or critical risk level.",
}


def make_authorization_decision(
    alignment_status: str,
    alignment_score: int,
    risk_level: str,
    risk_score: int,
    alignment_reason: str,
    risk_reason: str,
) -> dict:
    """
    Make an authorization decision based on goal alignment and risk assessment.

    Args:
        alignment_status: ALIGNED | PARTIALLY_ALIGNED | UNALIGNED
        alignment_score: 0-100
        risk_level: LOW | MEDIUM | HIGH | CRITICAL
        risk_score: 0-100
        alignment_reason: Reason from goal integrity engine
        risk_reason: Reason from risk engine

    Returns:
        dict with decision, reason, and detailed_reason
    """
    # Look up in decision matrix
    key = (alignment_status, risk_level)
    decision = DECISION_MATRIX.get(key, "BLOCK")  # Default to BLOCK if unknown

    # Build a detailed reason
    base_reason = DECISION_REASONS.get(decision, "Unknown decision.")

    detailed_parts = [base_reason]
    detailed_parts.append(f"Goal Alignment: {alignment_score}% ({alignment_status}).")
    detailed_parts.append(f"Risk Level: {risk_level} (score: {risk_score}).")

    if decision == "BLOCK":
        detailed_parts.append(f"Integrity: {alignment_reason}")
        detailed_parts.append(f"Risk: {risk_reason}")

    if decision == "REQUIRE_APPROVAL":
        detailed_parts.append(f"Review needed: {alignment_reason}")

    detailed_reason = " ".join(detailed_parts)

    return {
        "decision": decision,
        "reason": detailed_reason,
    }
