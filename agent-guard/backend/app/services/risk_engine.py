"""
Risk Engine — Deterministic risk classification for agent actions.

Maps action types to risk levels and scores.
Includes special-case overrides for sensitive targets.

Returns:
    riskLevel: LOW | MEDIUM | HIGH | CRITICAL
    riskScore: 0-100
    riskReason: explanation string
"""

# Base risk mapping by action type
# Includes both legacy format (READ_FILE, WRITE_FILE) and Antigravity normalizer format (FILE_READ, FILE_WRITE)
ACTION_RISK_MAP = {
    # Legacy format (simulated agent)
    "READ_FILE": {
        "riskLevel": "LOW",
        "riskScore": 10,
        "riskReason": "Reading a file is a safe, non-destructive operation."
    },
    "RUN_TESTS": {
        "riskLevel": "LOW",
        "riskScore": 15,
        "riskReason": "Running tests is a standard safe operation."
    },
    "WRITE_FILE": {
        "riskLevel": "MEDIUM",
        "riskScore": 40,
        "riskReason": "Writing a new file modifies the project structure."
    },
    "MODIFY_FILE": {
        "riskLevel": "MEDIUM",
        "riskScore": 50,
        "riskReason": "Modifying an existing file can introduce changes to the codebase."
    },
    "RUN_COMMAND": {
        "riskLevel": "HIGH",
        "riskScore": 70,
        "riskReason": "Running shell commands can have unpredictable system-level effects."
    },
    "DELETE_FILE": {
        "riskLevel": "HIGH",
        "riskScore": 80,
        "riskReason": "Deleting a file is a destructive, potentially irreversible action."
    },
    "EXTERNAL_UPLOAD": {
        "riskLevel": "HIGH",
        "riskScore": 75,
        "riskReason": "Uploading data externally risks data exfiltration."
    },
    "ACCESS_FILE": {
        "riskLevel": "MEDIUM",
        "riskScore": 45,
        "riskReason": "Accessing a file depends on the sensitivity of the target."
    },
    "DELETE_DATABASE": {
        "riskLevel": "CRITICAL",
        "riskScore": 100,
        "riskReason": "Deleting a database is an extremely destructive action."
    },
    # Antigravity normalizer format (agent-independent generic action types)
    "FILE_READ": {
        "riskLevel": "LOW",
        "riskScore": 10,
        "riskReason": "Reading a file is a safe, non-destructive operation."
    },
    "FILE_WRITE": {
        "riskLevel": "MEDIUM",
        "riskScore": 40,
        "riskReason": "Writing or modifying a file changes the project structure."
    },
    "FILE_DELETE": {
        "riskLevel": "HIGH",
        "riskScore": 80,
        "riskReason": "Deleting a file is a destructive, potentially irreversible action."
    },
    "COMMAND_EXECUTION": {
        "riskLevel": "HIGH",
        "riskScore": 70,
        "riskReason": "Running shell commands can have unpredictable system-level effects."
    },
    "EXTERNAL_TRANSACTION": {
        "riskLevel": "HIGH",
        "riskScore": 75,
        "riskReason": "External transactions involve real-world financial or irreversible actions."
    },
    "SECRET_ACCESS": {
        "riskLevel": "CRITICAL",
        "riskScore": 95,
        "riskReason": "Accessing secrets exposes API keys, passwords, and credentials."
    },
    "BROWSER_NAVIGATE": {
        "riskLevel": "LOW",
        "riskScore": 15,
        "riskReason": "Navigating to a URL is a low-risk investigative action."
    },
    "BROWSER_SEARCH": {
        "riskLevel": "LOW",
        "riskScore": 10,
        "riskReason": "Searching the web is a safe informational operation."
    },
    "API_REQUEST": {
        "riskLevel": "LOW",
        "riskScore": 20,
        "riskReason": "Fetching URL content is a read-only network operation."
    },
    "MCP_TOOL_CALL": {
        "riskLevel": "MEDIUM",
        "riskScore": 50,
        "riskReason": "MCP tool calls execute external integrations with variable risk."
    },
    "GENERAL_ACTION": {
        "riskLevel": "MEDIUM",
        "riskScore": 50,
        "riskReason": "Unknown action type; evaluated with moderate risk as a precaution."
    },
}

# Special target overrides — these override the base risk for specific targets
SENSITIVE_TARGETS = {
    ".env": {
        "riskLevel": "CRITICAL",
        "riskScore": 95,
        "riskReason": "Accessing .env exposes secrets, API keys, and credentials."
    },
    "package.json": {
        "riskLevel": "MEDIUM",
        "riskScore": 50,
        "riskReason": "Modifying package.json can alter project dependencies."
    },
    "database.sql": {
        "riskLevel": "CRITICAL",
        "riskScore": 90,
        "riskReason": "Operating on database files carries high data-loss risk."
    },
}


def evaluate_risk(action_type: str, target: str) -> dict:
    """
    Evaluate the risk level of a proposed action.

    Args:
        action_type: Type of action (READ_FILE, MODIFY_FILE, DELETE_FILE, etc.)
        target: Target file or resource name

    Returns:
        dict with riskLevel, riskScore, riskReason
    """
    action_upper = action_type.upper()
    target_lower = target.lower().strip()

    # Start with the base risk for this action type
    base = ACTION_RISK_MAP.get(action_upper, {
        "riskLevel": "MEDIUM",
        "riskScore": 50,
        "riskReason": f"Unknown action type: {action_type}."
    })

    result = dict(base)

    # Check for sensitive target overrides
    for sensitive_name, override in SENSITIVE_TARGETS.items():
        if sensitive_name in target_lower:
            # Use the higher risk between base and override
            if override["riskScore"] > result["riskScore"]:
                result = dict(override)
            break

    # Special case: DELETE_FILE on database-related targets → CRITICAL
    if action_upper == "DELETE_FILE" and any(
        kw in target_lower for kw in ["database", "db", ".sql"]
    ):
        result = {
            "riskLevel": "CRITICAL",
            "riskScore": 95,
            "riskReason": "Deleting a database file is a critical destructive action that can cause irreversible data loss."
        }

    # Special case: ACCESS_FILE on .env → CRITICAL
    return result


def get_cumulative_risk_level(score: int) -> str:
    """Map cumulative risk score to standard V5 levels."""
    if score <= 30:
        return "LOW"
    elif score <= 50:
        return "MODERATE"
    elif score <= 70:
        return "HIGH"
    return "CRITICAL"


def evaluate_cumulative_risk(
    action_history: list,
    current_action_risk: dict
) -> dict:
    """
    Evaluate cumulative risk trajectory across agent execution history.

    Args:
        action_history: List of past action dicts.
        current_action_risk: Result of evaluate_risk for the current action.

    Returns:
        dict with cumulativeRiskScore (0-100), cumulativeRiskLevel, cumulativeRiskReason
    """
    curr_score = current_action_risk.get("riskScore", 10)
    history_scores = [a.get("riskScore", 10) for a in action_history]
    all_scores = history_scores + [curr_score]

    reasons = []
    
    # Base: current action risk score weighted with maximum history risk
    max_history_risk = max(all_scores) if all_scores else curr_score
    recent_scores = all_scores[-3:] if len(all_scores) >= 3 else all_scores
    recent_avg = sum(recent_scores) / len(recent_scores)

    # Base formula: 40% current + 30% recent average + 30% peak risk
    cum_score = int((curr_score * 0.40) + (recent_avg * 0.30) + (max_history_risk * 0.30))

    # Escalation Factor 1: Consecutive high risk actions
    consecutive_high_risk = 0
    for s in reversed(all_scores):
        if s >= 60:
            consecutive_high_risk += 1
        else:
            break

    if consecutive_high_risk >= 2:
        escalation_bonus = consecutive_high_risk * 10
        cum_score += escalation_bonus
        reasons.append(f"Risk escalation detected ({consecutive_high_risk} consecutive high-risk operations)")

    # Escalation Factor 2: Blocked / Critical attempts in history
    blocked_count = sum(1 for a in action_history if a.get("decision") == "BLOCK")
    if blocked_count > 0:
        cum_score += min(25, blocked_count * 10)
        reasons.append(f"Cumulative risk elevated by {blocked_count} previous blocked security violations")

    # Escalation Factor 3: Touching sensitive credentials or database
    critical_attempts = sum(1 for a in action_history if a.get("riskLevel") == "CRITICAL")
    if current_action_risk.get("riskLevel") == "CRITICAL" or critical_attempts > 0:
        cum_score = max(cum_score, 85)
        reasons.append("Critical sensitive target accessed or attempted in session")

    # Clamp
    cum_score = max(0, min(100, cum_score))
    cum_level = get_cumulative_risk_level(cum_score)

    if not reasons:
        reasons.append(f"Cumulative risk is {cum_level.lower()} across {len(all_scores)} actions.")

    return {
        "cumulativeRiskScore": cum_score,
        "cumulativeRiskLevel": cum_level,
        "cumulativeRiskReason": ". ".join(reasons)
    }
