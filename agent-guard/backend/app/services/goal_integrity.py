"""
Goal Integrity Engine — Dynamic & Rule-based goal alignment scoring.

Evaluates whether a proposed action is related to the user's goal
and consistent with the dynamic Goal Policy.

Returns:
    goalAlignmentScore (0-100)
    alignmentStatus: ALIGNED | PARTIALLY_ALIGNED | UNALIGNED
    violatedConstraints: list of violated constraint strings
    reason: explanation string
"""

from typing import Dict, Any, List, Optional


def _extract_keywords(text: str) -> set:
    """Extract meaningful keywords from text, lowercased."""
    stop_words = {
        "the", "a", "an", "in", "my", "is", "to", "of", "and", "or",
        "for", "on", "at", "it", "do", "not", "be", "this", "that",
        "with", "from", "fix", "create", "make"
    }
    words = text.lower().replace(".", " ").replace(",", " ").split()
    return {w.strip() for w in words if w.strip() and w.strip() not in stop_words}


def evaluate_goal_integrity(
    user_goal: str,
    action_type: str,
    target: str,
    description: str,
    constraints: List[str] = None,
    goal_policy: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Evaluate whether an action aligns dynamically with the user's goal and Goal Policy.
    """
    if constraints is None:
        constraints = []

    score = 50  # Base score
    reasons = []
    violated_constraints = []

    action_upper = action_type.strip().upper()
    target_lower = target.strip().lower()
    desc_lower = description.strip().lower()
    combined = f"{action_upper} {target_lower} {desc_lower}"

    # Extract dynamic policy scope lists
    allowed_scope = [s.lower() for s in goal_policy.get("allowedScope", [])] if goal_policy else []
    restricted_scope = [s.lower() for s in goal_policy.get("restrictedScope", [])] if goal_policy else []
    all_constraints = list(set(constraints + (goal_policy.get("constraints", []) if goal_policy else [])))

    # 1. Dynamic Restricted Scope Check
    for restricted in restricted_scope:
        if restricted in target_lower or restricted in combined:
            score -= 40
            reason_msg = f"Target touches restricted scope: '{restricted}'"
            reasons.append(reason_msg)
            violated_constraints.append(f"Restricted scope: {restricted}")

    # 2. Dynamic Allowed Scope Match
    if allowed_scope:
        matches_allowed = any(
            allowed in target_lower or allowed in combined or allowed in ("project files", "all files", "general task")
            for allowed in allowed_scope
        )
        if matches_allowed:
            score += 25
            reasons.append("Action operates within allowed scope")
        else:
            score -= 10
            reasons.append("Action is outside primary allowed scope")
    else:
        score += 15

    # 3. Explicit User Constraint Check
    for c in all_constraints:
        c_lower = c.lower()

        # "Do not delete files" + DELETE_FILE → violation
        if "delete" in c_lower and "delete" in action_upper.lower():
            score -= 45
            violated_constraints.append(c)
            reasons.append(f"Violates constraint: \"{c}\"")

        # "Do not access secrets" / "secret" / "env"
        elif ("secret" in c_lower or "env" in c_lower) and (".env" in target_lower or "secret" in target_lower or "access" in action_upper.lower()):
            score -= 45
            violated_constraints.append(c)
            reasons.append(f"Violates constraint: \"{c}\"")

        # "Do not modify backend" / "backend"
        elif "backend" in c_lower and ("backend" in target_lower or "server" in target_lower):
            score -= 40
            violated_constraints.append(c)
            reasons.append(f"Violates constraint: \"{c}\"")

        # "Do not change database schema" / "schema"
        elif "schema" in c_lower and ("schema" in target_lower or "database.sql" in target_lower or "sql" in target_lower):
            score -= 40
            violated_constraints.append(c)
            reasons.append(f"Violates constraint: \"{c}\"")

        # "Do not upload externally" / "upload"
        elif "upload" in c_lower and ("upload" in target_lower or "upload" in action_upper.lower() or "external" in combined):
            score -= 45
            violated_constraints.append(c)
            reasons.append(f"Violates constraint: \"{c}\"")

    # 4. Keyword and Target Relevance Match with User Goal
    goal_keywords = _extract_keywords(user_goal)
    target_words = set(target_lower.replace(".", " ").replace("/", " ").replace("_", " ").split())
    matches = goal_keywords & target_words
    if matches or target_lower in user_goal.lower():
        score += 25
        reasons.append(f"Target matches goal: {target}")

    # 5. Standard Action Type Heuristics
    if action_upper in ("READ_FILE", "FILE_READ"):
        score += 15
        reasons.append("Reading files is a safe investigative action")
    elif action_upper in ("RUN_TESTS",):
        score += 15
        reasons.append("Running tests verifies software correctness")
    elif action_upper in ("MODIFY_FILE", "WRITE_FILE", "FILE_WRITE") and not violated_constraints:
        if matches or target_lower in user_goal.lower() or any(w in desc_lower for w in goal_keywords):
            score += 25
            reasons.append("File modification directly accomplishes user goal")
        elif allowed_scope and any(allowed in target_lower for allowed in allowed_scope if allowed not in ("project files", "all files")):
            score += 20
            reasons.append("File write is within designated allowed scope")
        elif not matches and len(goal_keywords) > 0:
            score -= 15
            reasons.append("File write does not clearly match active goal objectives")
    elif action_upper in ("DELETE_FILE", "FILE_DELETE") and not violated_constraints:
        # Contextual check: If goal explicitly mentions deleting files
        if "delete" in user_goal.lower() or "clean" in user_goal.lower() or "remove" in user_goal.lower():
            score += 20
            reasons.append("File deletion is consistent with user goal objective")
        else:
            score -= 25
            reasons.append("Deleting files requires explicit authorization")
    elif action_upper in ("BROWSER_NAVIGATE", "BROWSER_SEARCH", "API_REQUEST"):
        score += 15
        reasons.append("Browser exploration / information gathering is low-risk")
    elif action_upper in ("EXTERNAL_TRANSACTION",):
        score -= 20
        reasons.append("External transaction requires user confirmation")
    elif action_upper in ("SECRET_ACCESS",):
        score -= 50
        violated_constraints.append("Secret / credential access prohibited")
        reasons.append("Accessing confidential secrets is restricted")

    # Clamp score to 0–100
    score = max(0, min(100, score))

    if score >= 80:
        status = "ALIGNED"
    elif score >= 50:
        status = "PARTIALLY_ALIGNED"
    else:
        status = "UNALIGNED"

    reason_str = ". ".join(reasons) + "." if reasons else "Action evaluated against dynamic goal policy."

    return {
        "goalAlignmentScore": score,
        "alignmentStatus": status,
        "violatedConstraints": list(set(violated_constraints)),
        "reason": reason_str,
    }
