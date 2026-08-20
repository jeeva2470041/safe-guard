"""
Risk Engine — Deterministic risk classification for agent actions.

Maps action types to risk levels and scores.
Includes special-case overrides for sensitive targets and real-world task categories.

Phase 1 & Phase 2 Support:
- Consequence Categories: LOW | MEDIUM | HIGH | CRITICAL
- Expanded Browser, API, Email, Financial, Forms, and MCP tool actions
- Sensitive overrides (SSH keys, cookies, credentials, database destruction)

Returns:
    riskLevel: LOW | MEDIUM | HIGH | CRITICAL
    riskScore: 0-100
    riskReason: explanation string
"""

# Base risk mapping by canonical and legacy action types
ACTION_RISK_MAP = {
    # ── Real-World Browser Actions ──
    "BROWSER_SEARCH": {
        "riskLevel": "LOW",
        "riskScore": 10,
        "riskReason": "Searching the web is a safe informational operation."
    },
    "BROWSER_NAVIGATE": {
        "riskLevel": "LOW",
        "riskScore": 15,
        "riskReason": "Navigating to a public URL is a read-only informational action."
    },
    "BROWSER_READ_PAGE": {
        "riskLevel": "LOW",
        "riskScore": 10,
        "riskReason": "Reading public web page text leaves host state unchanged."
    },
    "BROWSER_EXTRACT": {
        "riskLevel": "LOW",
        "riskScore": 10,
        "riskReason": "Extracting structured data from web pages is a safe read operation."
    },
    "BROWSER_CLICK": {
        "riskLevel": "LOW",
        "riskScore": 15,
        "riskReason": "Clicking page elements (selecting seats, flights, filters) is a safe navigation action."
    },
    "BROWSER_SELECT": {
        "riskLevel": "LOW",
        "riskScore": 15,
        "riskReason": "Selecting options in dropdowns is a routine user navigation action."
    },
    "BROWSER_TYPE": {
        "riskLevel": "LOW",
        "riskScore": 20,
        "riskReason": "Filling form fields with requested details is a routine web action."
    },
    "BROWSER_DOWNLOAD": {
        "riskLevel": "MEDIUM",
        "riskScore": 35,
        "riskReason": "Downloading web resources saves files to local storage."
    },
    "BROWSER_SUBMIT": {
        "riskLevel": "MEDIUM",
        "riskScore": 45,
        "riskReason": "Submitting a web form transmits input data to target web service."
    },
    "BROWSER_UPLOAD": {
        "riskLevel": "HIGH",
        "riskScore": 75,
        "riskReason": "Uploading files to external services carries data exfiltration risks."
    },

    # ── Financial Actions ──
    "FINANCIAL_VIEW_PRICE": {
        "riskLevel": "LOW",
        "riskScore": 10,
        "riskReason": "Viewing product or ticket pricing is a read-only operation."
    },
    "FINANCIAL_SELECT_PAYMENT": {
        "riskLevel": "MEDIUM",
        "riskScore": 40,
        "riskReason": "Selecting a payment method configures transaction checkout options."
    },
    "FINANCIAL_INITIATE_PAYMENT": {
        "riskLevel": "HIGH",
        "riskScore": 75,
        "riskReason": "Initiating payment commits financial charges and mandates human authorization."
    },
    "FINANCIAL_CONFIRM_PAYMENT": {
        "riskLevel": "HIGH",
        "riskScore": 75,
        "riskReason": "Final payment confirmation executes financial transactions."
    },
    "EXTERNAL_TRANSACTION": {
        "riskLevel": "HIGH",
        "riskScore": 75,
        "riskReason": "External transactions involve monetary charge or irreversible financial commitments."
    },

    # ── Email Actions ──
    "EMAIL_READ": {
        "riskLevel": "LOW",
        "riskScore": 10,
        "riskReason": "Reading email messages is a read-only operation."
    },
    "EMAIL_COMPOSE": {
        "riskLevel": "LOW",
        "riskScore": 20,
        "riskReason": "Drafting an email creates local text without external transmission."
    },
    "EMAIL_ATTACH": {
        "riskLevel": "MEDIUM",
        "riskScore": 35,
        "riskReason": "Attaching files stages local documents for transmission."
    },
    "EMAIL_SEND": {
        "riskLevel": "MEDIUM",
        "riskScore": 55,
        "riskReason": "Transmitting external emails communicates outside the local system."
    },
    "EXTERNAL_COMMUNICATION": {
        "riskLevel": "MEDIUM",
        "riskScore": 55,
        "riskReason": "Transmitting external communication sends data outside the local workspace."
    },

    # ── Form Actions ──
    "FORM_FILL": {
        "riskLevel": "LOW",
        "riskScore": 20,
        "riskReason": "Populating form fields with user data is standard routine operation."
    },
    "FORM_SUBMIT": {
        "riskLevel": "MEDIUM",
        "riskScore": 45,
        "riskReason": "Submitting forms transmits data to third-party endpoints."
    },

    # ── REST API Actions ──
    "API_GET": {
        "riskLevel": "LOW",
        "riskScore": 15,
        "riskReason": "HTTP GET requests are read-only and idempotent."
    },
    "API_POST": {
        "riskLevel": "MEDIUM",
        "riskScore": 45,
        "riskReason": "HTTP POST creates or mutates remote state."
    },
    "API_PUT": {
        "riskLevel": "MEDIUM",
        "riskScore": 45,
        "riskReason": "HTTP PUT updates remote resources."
    },
    "API_PATCH": {
        "riskLevel": "MEDIUM",
        "riskScore": 40,
        "riskReason": "HTTP PATCH modifies remote resource fields."
    },
    "API_DELETE": {
        "riskLevel": "HIGH",
        "riskScore": 80,
        "riskReason": "HTTP DELETE deletes remote server data."
    },
    "API_REQUEST": {
        "riskLevel": "LOW",
        "riskScore": 20,
        "riskReason": "Fetching URL or API content is a read-only network operation."
    },

    # ── MCP Tool Actions ──
    "MCP_DISCOVERY": {
        "riskLevel": "LOW",
        "riskScore": 10,
        "riskReason": "Listing available MCP tools and resources is read-only discovery."
    },
    "MCP_RESOURCE_READ": {
        "riskLevel": "LOW",
        "riskScore": 15,
        "riskReason": "Reading MCP resources is safe inspection."
    },
    "MCP_INVOCATION": {
        "riskLevel": "MEDIUM",
        "riskScore": 45,
        "riskReason": "Invoking MCP tools executes external integrations."
    },
    "MCP_RESOURCE_WRITE": {
        "riskLevel": "HIGH",
        "riskScore": 75,
        "riskReason": "Writing MCP resources mutates external server state."
    },

    # ── Filesystem & Command Actions ──
    "FILE_READ": {
        "riskLevel": "LOW",
        "riskScore": 10,
        "riskReason": "Reading a file is a safe, non-destructive operation."
    },
    "READ_FILE": {
        "riskLevel": "LOW",
        "riskScore": 10,
        "riskReason": "Reading a file is a safe, non-destructive operation."
    },
    "FILE_WRITE": {
        "riskLevel": "MEDIUM",
        "riskScore": 40,
        "riskReason": "Writing or modifying a file changes the project structure."
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
    "RUN_TESTS": {
        "riskLevel": "LOW",
        "riskScore": 15,
        "riskReason": "Running tests is a standard safe verification operation."
    },
    "FILE_DELETE": {
        "riskLevel": "HIGH",
        "riskScore": 80,
        "riskReason": "Deleting a file is a destructive, potentially irreversible action."
    },
    "DELETE_FILE": {
        "riskLevel": "HIGH",
        "riskScore": 80,
        "riskReason": "Deleting a file is a destructive, potentially irreversible action."
    },
    "COMMAND_EXECUTION": {
        "riskLevel": "HIGH",
        "riskScore": 70,
        "riskReason": "Running shell commands can have unpredictable system-level effects."
    },
    "RUN_COMMAND": {
        "riskLevel": "HIGH",
        "riskScore": 70,
        "riskReason": "Running shell commands can have unpredictable system-level effects."
    },
    "SECRET_ACCESS": {
        "riskLevel": "CRITICAL",
        "riskScore": 95,
        "riskReason": "Accessing secrets exposes private keys, API keys, passwords, or cookies."
    },
    "DELETE_DATABASE": {
        "riskLevel": "CRITICAL",
        "riskScore": 100,
        "riskReason": "Deleting a database is an extremely destructive action."
    },
    "EXTERNAL_UPLOAD": {
        "riskLevel": "HIGH",
        "riskScore": 75,
        "riskReason": "Uploading data externally risks data exfiltration."
    },
    "GENERAL_ACTION": {
        "riskLevel": "MEDIUM",
        "riskScore": 35,
        "riskReason": "Standard automated agent action."
    },
}

# Special target overrides
SENSITIVE_TARGETS = {
    ".env": {
        "riskLevel": "CRITICAL",
        "riskScore": 95,
        "riskReason": "Accessing .env exposes secrets, API keys, and credentials."
    },
    "id_rsa": {
        "riskLevel": "CRITICAL",
        "riskScore": 98,
        "riskReason": "Accessing private SSH key exposes host infrastructure to unauthorized takeover."
    },
    "id_ed25519": {
        "riskLevel": "CRITICAL",
        "riskScore": 98,
        "riskReason": "Accessing private SSH key exposes host infrastructure to unauthorized takeover."
    },
    "cookie": {
        "riskLevel": "CRITICAL",
        "riskScore": 95,
        "riskReason": "Accessing or exfiltrating browser cookies compromises user active sessions."
    },
    "package.json": {
        "riskLevel": "HIGH",
        "riskScore": 70,
        "riskReason": "Modifying package.json alters project dependencies and manifest configuration."
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
    Distinguishes simple routine tasks from high-impact operations and critical security threats.
    """
    action_upper = action_type.upper()
    target_lower = target.lower().strip()

    base = ACTION_RISK_MAP.get(action_upper, {
        "riskLevel": "MEDIUM",
        "riskScore": 35,
        "riskReason": f"Standard action type: {action_type}."
    })

    result = dict(base)

    # 1. Check for sensitive target overrides
    for sensitive_name, override in SENSITIVE_TARGETS.items():
        if sensitive_name in target_lower:
            if override["riskScore"] > result["riskScore"]:
                result = dict(override)
            break

    # 2. Smart Command Execution Risk Classification
    if action_upper in ("RUN_COMMAND", "COMMAND_EXECUTION"):
        if any(crit in target_lower for crit in ("rm -rf /", "rm -rf c:", "format ", "drop database", "cat .env", "type .env", "printenv", "echo $", "id_rsa", "cat ~/.ssh")):
            result = {
                "riskLevel": "CRITICAL",
                "riskScore": 95,
                "riskReason": "Destructive system wipe or credential exposure command."
            }
        elif any(high in target_lower for high in ("npm install", "pip install", "npm uninstall", "pip uninstall", "git push", "git reset", "git clean", "chmod -r", "chown", "systemctl", "netsh")):
            result = {
                "riskLevel": "HIGH",
                "riskScore": 75,
                "riskReason": "High-impact command modifying dependencies, remote repository, or system environment."
            }
        elif any(
            target_lower.startswith(p)
            for p in (
                "git status", "git log", "git diff", "git branch", "git show",
                "dir", "ls", "pwd", "get-childitem", "test-path", "cat ", "type ",
                "head ", "tail ", "get-process", "echo ", "which ", "where ", "get-command",
                "pytest", "npm test", "vitest", "jest", "npm run build", "npm run lint", "tsc",
                "python -c \"import", "python -m pytest", "python debug", "python -c \"", "node -v", "python --version"
            )
        ):
            result = {
                "riskLevel": "LOW",
                "riskScore": 15,
                "riskReason": "Standard read-only diagnostic, verification, or build command."
            }
        else:
            result = {
                "riskLevel": "MEDIUM",
                "riskScore": 35,
                "riskReason": "Routine local development command execution."
            }

    # 3. Smart File Deletion Risk Classification
    if action_upper in ("DELETE_FILE", "FILE_DELETE"):
        if any(kw in target_lower for kw in ["database", "db", ".sql", ".env", "credentials", "id_rsa"]):
            result = {
                "riskLevel": "CRITICAL",
                "riskScore": 95,
                "riskReason": "Deleting a database or credential file is a critical destructive action that can cause irreversible data loss."
            }
        elif any(kw in target_lower for kw in ["package.json", "dockerfile", "docker-compose", "schema", "config", "settings", ".git"]):
            result = {
                "riskLevel": "HIGH",
                "riskScore": 80,
                "riskReason": "Deleting configuration or dependency manifests carries high risk."
            }
        else:
            result = {
                "riskLevel": "LOW",
                "riskScore": 25,
                "riskReason": "Deleting temporary, scratch, or requested file is safe."
            }

    # 4. Smart File Write Risk Classification
    if action_upper in ("WRITE_FILE", "MODIFY_FILE", "FILE_WRITE"):
        if any(kw in target_lower for kw in [".env", "id_rsa", "credentials", "secrets"]):
            result = {
                "riskLevel": "CRITICAL",
                "riskScore": 95,
                "riskReason": "Attempting to modify or overwrite secret configuration files."
            }
        elif any(kw in target_lower for kw in ["package.json", "pom.xml", "settings.py", "dockerfile"]):
            result = {
                "riskLevel": "HIGH",
                "riskScore": 70,
                "riskReason": "Modifying dependency files alters project build manifests."
            }
        elif any(kw in target_lower for kw in [".jsx", ".tsx", ".vue", ".html", ".css", "styles", "component", "page", "button", "header", "footer", "card"]):
            result = {
                "riskLevel": "LOW",
                "riskScore": 25,
                "riskReason": "Standard frontend UI component editing is low-risk."
            }

    return result


def evaluate_cumulative_risk(previous_actions: list, current_action_risk: dict) -> dict:
    """
    Calculate cumulative session risk score based on action history and escalation trends.
    """
    if not previous_actions:
        return {
            "cumulativeRiskScore": current_action_risk["riskScore"],
            "cumulativeRiskLevel": current_action_risk["riskLevel"],
            "escalationDetected": False
        }

    high_risk_count = sum(1 for a in previous_actions if a.get("riskLevel") in ("HIGH", "CRITICAL"))
    blocked_count = sum(1 for a in previous_actions if a.get("decision") == "BLOCK")

    base_score = current_action_risk["riskScore"]
    penalty = (high_risk_count * 10) + (blocked_count * 15)
    cum_score = min(100, base_score + penalty)

    if cum_score >= 80:
        level = "CRITICAL"
    elif cum_score >= 60:
        level = "HIGH"
    elif cum_score >= 35:
        level = "MEDIUM"
    else:
        level = "LOW"

    return {
        "cumulativeRiskScore": cum_score,
        "cumulativeRiskLevel": level,
        "escalationDetected": (blocked_count >= 2 or high_risk_count >= 3)
    }


def get_cumulative_risk_level(score: int) -> str:
    """Helper to convert numeric cumulative risk score to string level."""
    if score >= 80:
        return "CRITICAL"
    elif score >= 60:
        return "HIGH"
    elif score >= 35:
        return "MEDIUM"
    return "LOW"
