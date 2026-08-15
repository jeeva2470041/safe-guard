"""
Goal Drift Engine — Advanced Multi-Step Goal Drift Detection & Trajectory Analysis.

Evaluates not only the current action but the rolling multi-step trajectory
of recent agent actions to detect when an agent is progressively moving away
from the user's established Goal Policy.

Drift Score Ranges (0–100):
  0–20:   NORMAL
  21–40:  LOW
  41–60:  MODERATE
  61–80:  HIGH
  81–100: CRITICAL
"""

from typing import Dict, Any, List, Optional


def get_drift_level(score: int) -> str:
    """Map numeric drift score (0-100) to standard V5 drift level."""
    if score <= 20:
        return "NORMAL"
    elif score <= 40:
        return "LOW"
    elif score <= 60:
        return "MODERATE"
    elif score <= 80:
        return "HIGH"
    return "CRITICAL"


def calculate_rolling_integrity(action_history: List[Dict[str, Any]], current_score: Optional[int] = None) -> float:
    """
    Calculate rolling goal integrity across agent execution history.
    Uses exponential decay weighting (more recent actions have higher weight).
    """
    all_scores = [a.get("goalAlignmentScore", 100) for a in action_history]
    if current_score is not None:
        all_scores.append(current_score)

    if not all_scores:
        return 100.0

    # Exponentially weighted rolling average
    weights = [1.0 + (i * 0.25) for i in range(len(all_scores))]
    weighted_sum = sum(s * w for s, w in zip(all_scores, weights))
    total_weight = sum(weights)

    return round(weighted_sum / total_weight, 1)


def detect_goal_drift(
    goal_policy: Dict[str, Any],
    previous_actions: List[Dict[str, Any]],
    proposed_action: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Multi-step goal drift evaluation combining:
    1. Direct scope and constraint divergence of the proposed action.
    2. Historical trajectory and recent action alignment degradation.
    3. Consecutive unaligned action streaks and scope jumping.
    """
    if not goal_policy:
        return {
            "driftScore": 0,
            "driftLevel": "NORMAL",
            "driftDetected": False,
            "rollingIntegrity": 100.0,
            "reason": "Initial baseline action with active policy."
        }

    action_type = proposed_action.get("actionType", "").upper()
    target = proposed_action.get("target", "").lower()
    description = proposed_action.get("description", "").lower()
    combined = f"{action_type} {target} {description}"

    restricted_scope = [s.lower() for s in goal_policy.get("restrictedScope", [])]
    allowed_scope = [s.lower() for s in goal_policy.get("allowedScope", [])]
    constraints = [c.lower() for c in goal_policy.get("constraints", [])]

    base_drift = 0
    reasons = []

    # ── Factor 1: Proposed Action Scope & Constraint Divergence ──
    for restricted in restricted_scope:
        if restricted in target or restricted in combined:
            base_drift += 65
            reasons.append(f"Targets restricted scope: '{restricted}'")
            break

    for constraint in constraints:
        if "backend" in constraint and ("backend" in target or "server" in target):
            base_drift += 50
            reasons.append(f"Violates constraint: '{constraint}'")
        elif "schema" in constraint and ("schema" in target or "sql" in target or "database" in target):
            base_drift += 50
            reasons.append(f"Violates constraint: '{constraint}'")
        elif "upload" in constraint and ("upload" in target or "external" in combined):
            base_drift += 60
            reasons.append(f"Violates constraint: '{constraint}'")
        elif ("secret" in constraint or "env" in constraint) and (".env" in target or "secret" in target or "credentials" in target):
            base_drift += 65
            reasons.append(f"Touches secret resource prohibited by: '{constraint}'")

    matches_allowed = any(
        allowed in target or allowed in combined or allowed in ("project files", "all files", "general task")
        for allowed in allowed_scope
    ) if allowed_scope else True

    if not matches_allowed and base_drift == 0:
        base_drift += 25
        reasons.append("Action operates outside primary allowed scope")

    # ── Factor 2: Historical Multi-Step Trajectory Analysis ──
    history_len = len(previous_actions)
    recent_actions = previous_actions[-4:] if history_len > 4 else previous_actions

    # Check recent alignment decline
    if recent_actions:
        recent_scores = [a.get("goalAlignmentScore", 100) for a in recent_actions]
        recent_avg = sum(recent_scores) / len(recent_scores)
        
        # If recent average is below 60, add trajectory drift
        if recent_avg < 50:
            base_drift += 30
            reasons.append(f"Recent action trajectory is severely degraded (avg alignment: {int(recent_avg)}%)")
        elif recent_avg < 75:
            base_drift += 15
            reasons.append(f"Recent actions exhibit declining goal alignment ({int(recent_avg)}%)")

        # Check consecutive unaligned streak
        unaligned_streak = 0
        for act in reversed(previous_actions):
            if act.get("decision") in ("BLOCK", "REJECTED") or act.get("goalAlignmentScore", 100) < 60:
                unaligned_streak += 1
            else:
                break

        if unaligned_streak >= 2:
            base_drift += (unaligned_streak * 12)
            reasons.append(f"{unaligned_streak} consecutive unaligned actions in recent trajectory")

    # ── Factor 3: Total Blocked / High-Risk History ──
    total_blocked = sum(1 for a in previous_actions if a.get("decision") in ("BLOCK", "REJECTED"))
    if total_blocked > 0:
        base_drift += min(20, total_blocked * 8)

    # Final score clamping
    drift_score = max(0, min(100, base_drift))
    drift_level = get_drift_level(drift_score)
    drift_detected = drift_score >= 41  # MODERATE, HIGH, CRITICAL

    # Rolling integrity estimate
    rolling_integrity = calculate_rolling_integrity(previous_actions)

    reason_str = ". ".join(reasons) + "." if reasons else "Action is within expected goal trajectory."

    return {
        "driftScore": drift_score,
        "driftLevel": drift_level,
        "driftDetected": drift_detected,
        "rollingIntegrity": rolling_integrity,
        "reason": reason_str
    }
