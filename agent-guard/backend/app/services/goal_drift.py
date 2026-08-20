"""
Goal Drift & Goal Hijacking Engine — Phase 3.

Evaluates multi-step goal drift and detects runtime Goal Hijacking:
- Rolling trajectory analysis across action history
- Objective Transition Detection: detects when the agent moves from legitimate domain tasks
  to unrelated objectives (e.g. flight search -> download tool -> steal cookies)
- Domain Category Jump Scoring: quantifies categorical divergence across sequential actions
- Hijacking Alerting: calculates goal hijacking confidence and triggers containment

Drift Score Ranges (0–100):
  0–20:   NORMAL
  21–40:  LOW
  41–60:  MODERATE
  61–80:  HIGH
  81–100: CRITICAL (GOAL HIJACKED)
"""

from typing import Dict, Any, List, Optional


# Domain categories for category-jump analysis (ordered by priority)
ACTION_DOMAIN_CATEGORIES = {
    "CREDENTIALS": ["cookie", "cookies.sqlite", ".env", "id_rsa", "id_ed25519", "credentials", "secrets", "token", "password", "shadow"],
    "SYSTEM_ADMIN": ["sudo", "systemctl", "netsh", "chmod", "chown", "adduser", "passwd", "rm -rf"],
    "TRAVEL": ["flight", "hotel", "seat", "passenger", "ticket", "airline", "indigo", "expedia", "booking"],
    "DEVELOPMENT": ["react", "frontend", "login.jsx", "portfolio", "button", "component", "css", "html", "javascript", "src/"],
    "DATABASE": ["database.sql", "schema.sql", "postgres", "mongo", "mysql", "sqlite", "table", "sql"],
    "GENERIC_TOOLS": ["calculator", "weather", "translate", "search_web", "read_url"]
}


def classify_action_domain(action_type: str, target: str, description: str) -> str:
    """Classifies an individual action into a domain category."""
    combined = f"{action_type} {target} {description}".lower()
    for cat, keywords in ACTION_DOMAIN_CATEGORIES.items():
        if any(kw in combined for kw in keywords):
            return cat
    return "GENERAL"


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
    4. Goal Hijacking Detection: category transition divergence.
    """
    if not goal_policy:
        return {
            "driftScore": 0,
            "driftLevel": "NORMAL",
            "driftDetected": False,
            "isGoalHijacked": False,
            "hijackingConfidence": 0.0,
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
    user_goal = goal_policy.get("original_goal") or goal_policy.get("userGoal") or goal_policy.get("objective") or ""

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

    if recent_actions:
        recent_scores = [a.get("goalAlignmentScore", 100) for a in recent_actions]
        recent_avg = sum(recent_scores) / len(recent_scores)
        
        if recent_avg < 50:
            base_drift += 30
            reasons.append(f"Recent action trajectory is severely degraded (avg alignment: {int(recent_avg)}%)")
        elif recent_avg < 75:
            base_drift += 15
            reasons.append(f"Recent actions exhibit declining goal alignment ({int(recent_avg)}%)")

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

    # ── Factor 4: Goal Hijacking & Domain Category Transition Analysis ──
    is_hijacked = False
    hijacking_confidence = 0.0
    
    proposed_domain = classify_action_domain(action_type, target, description)
    initial_domain = "GENERAL"
    if user_goal:
        initial_domain = classify_action_domain("GOAL", user_goal, "")

    # If goal is Travel/Frontend, but proposed action targets CREDENTIALS, SYSTEM_ADMIN, or unaligned DATABASE
    if initial_domain in ("TRAVEL", "DEVELOPMENT") and proposed_domain in ("CREDENTIALS", "SYSTEM_ADMIN", "DATABASE"):
        base_drift = max(base_drift + 55, 80)
        is_hijacked = True
        hijacking_confidence = max(hijacking_confidence, 0.85)
        reasons.append(f"Goal Hijacking Detected: Abrupt transition from '{initial_domain}' goal to unauthorized '{proposed_domain}' action.")

    # Check for trajectory domain shift (e.g. Action 1: Travel, Action 2: Download, Action 3: Credentials)
    if previous_actions:
        history_domains = [classify_action_domain(a.get("actionType", ""), a.get("target", ""), a.get("description", "")) for a in previous_actions]
        if len(set(history_domains)) >= 2 and proposed_domain in ("CREDENTIALS", "SYSTEM_ADMIN"):
            is_hijacked = True
            hijacking_confidence = max(hijacking_confidence, 0.9)
            base_drift += 40
            reasons.append("Multi-step Goal Hijacking Trajectory confirmed across divergent domain stages.")

    # Final score clamping
    drift_score = max(0, min(100, base_drift))
    drift_level = get_drift_level(drift_score)
    drift_detected = drift_score >= 41  # MODERATE, HIGH, CRITICAL

    if drift_score >= 80:
        is_hijacked = True
        hijacking_confidence = max(hijacking_confidence, 0.8)

    # Rolling integrity estimate
    rolling_integrity = calculate_rolling_integrity(previous_actions)

    reason_str = ". ".join(reasons) + "." if reasons else "Action is within expected goal trajectory."

    return {
        "driftScore": drift_score,
        "driftLevel": drift_level,
        "driftDetected": drift_detected,
        "isGoalHijacked": is_hijacked,
        "hijackingConfidence": round(hijacking_confidence, 2),
        "rollingIntegrity": rolling_integrity,
        "reason": reason_str
    }
