"""
Data Exfiltration Chain Detection Service — Phase 3.

Detects coordinated multi-step data exfiltration sequences:
1. Sensitive data / credential read (e.g. read .env, view database.sql, read cookies)
2. Data extraction / archiving / base64 encoding (e.g. tar, zip, base64, grep tokens)
3. External destination staging (e.g. curl endpoint, pastebin, webhook, s3 bucket)
4. Data transfer / upload (e.g. browser_upload, HTTP POST, curl -d @file)

Correlates action history across a session to compute chain confidence and prevent exfiltration.
"""

import re
from typing import Dict, Any, List, Optional, Tuple


EXFILTRATION_TARGET_PATTERNS = [
    (r"https?://(webhook\.site|requestbin|ngrok\.io|pipedream|pastebin|temp\.sh|file\.io|transfer\.sh)", "KNOWN_EXFIL_ENDPOINT"),
    (r"https?://\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(:\d+)?", "RAW_IP_ENDPOINT"),
    (r"s3://[a-zA-Z0-9\.\-]+", "CLOUD_STORAGE_BUCKET"),
    (r"gs://[a-zA-Z0-9\.\-]+", "GCS_STORAGE_BUCKET"),
]

SENSITIVE_DATA_KEYWORDS = [
    ".env", "id_rsa", "id_ed25519", "cookie", "cookies.sqlite", "shadow", "password",
    "database.sql", "schema.sql", "credentials", "secrets", "api_key", "token", "auth"
]

ENCODING_OR_ARCHIVE_KEYWORDS = [
    "base64", "tar", "zip", "gzip", "bzip2", "7z", "compress", "encode", "btoa"
]

TRANSFER_ACTION_TYPES = [
    "EXTERNAL_UPLOAD", "BROWSER_UPLOAD", "API_POST", "API_PUT", "EMAIL_SEND",
    "COMMAND_EXECUTION", "RUN_COMMAND"
]


def is_sensitive_access_action(action: Dict[str, Any]) -> bool:
    """Checks if an action involves reading or accessing sensitive data."""
    act_type = str(action.get("actionType", "")).upper()
    target = str(action.get("target", "")).lower()
    desc = str(action.get("description", "")).lower()
    combined = f"{target} {desc}"

    if act_type in ("SECRET_ACCESS", "FILE_READ", "READ_FILE", "MCP_RESOURCE_READ"):
        if any(sens in combined for sens in SENSITIVE_DATA_KEYWORDS):
            return True
    return False


def is_encoding_action(action: Dict[str, Any]) -> bool:
    """Checks if an action involves encoding, archiving, or preparing data."""
    desc = str(action.get("description", "")).lower()
    target = str(action.get("target", "")).lower()
    combined = f"{target} {desc}"
    return any(enc in combined for enc in ENCODING_OR_ARCHIVE_KEYWORDS)


def is_outbound_transfer_action(action: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """Checks if an action attempts to send data to an external destination."""
    act_type = str(action.get("actionType", "")).upper()
    target = str(action.get("target", "")).lower()
    desc = str(action.get("description", "")).lower()
    combined = f"{target} {desc}"

    if act_type in ("EXTERNAL_UPLOAD", "BROWSER_UPLOAD", "API_POST", "API_PUT"):
        return True, "OUTBOUND_API_OR_UPLOAD"

    if act_type in ("COMMAND_EXECUTION", "RUN_COMMAND"):
        if any(cmd in combined for cmd in ("curl -d", "curl -f", "curl -x post", "wget --post", "nc -w", "scp ", "rsync ")):
            return True, "SHELL_OUTBOUND_COMMAND"

    # Check for known exfil endpoints
    for pattern, endpoint_type in EXFILTRATION_TARGET_PATTERNS:
        if re.search(pattern, combined):
            return True, endpoint_type

    return False, None


def detect_exfiltration_chain(
    previous_actions: List[Dict[str, Any]],
    current_action: Dict[str, Any],
    user_goal: str = ""
) -> Dict[str, Any]:
    """
    Evaluates whether the proposed action forms part of an active data exfiltration chain.
    """
    all_actions = list(previous_actions) + [current_action]
    
    # 1. Identify chain links
    sensitive_reads = [a for a in all_actions if is_sensitive_access_action(a)]
    encoding_steps = [a for a in all_actions if is_encoding_action(a)]
    
    is_transfer, transfer_type = is_outbound_transfer_action(current_action)

    # 2. Check if current action completes an exfiltration sequence
    chain_links = []
    exfil_detected = False
    severity = "LOW"
    decision = "ALLOW"
    reason = "No data exfiltration chain detected."

    if sensitive_reads:
        chain_links.append(f"Link 1: Sensitive data access ({len(sensitive_reads)} action(s))")

    if encoding_steps:
        chain_links.append(f"Link 2: Data encoding/compression ({len(encoding_steps)} action(s))")

    if is_transfer:
        chain_links.append(f"Link 3: Outbound transmission attempt ({transfer_type})")

    # If sensitive read preceded an outbound transfer
    if sensitive_reads and is_transfer:
        exfil_detected = True
        if encoding_steps:
            # 3-link chain (Read -> Encode -> Upload): High confidence attack
            severity = "CRITICAL"
            decision = "BLOCK"
            reason = (
                f"Data Exfiltration Chain Detected (Read -> Encode -> Outbound Transfer). "
                f"Target '{current_action.get('target')}' preceded by sensitive data read '{sensitive_reads[0].get('target')}'. Blocked."
            )
        else:
            # 2-link chain (Read -> Direct Upload): Critical if secrets, High if files
            severity = "CRITICAL"
            decision = "BLOCK"
            reason = (
                f"Direct Data Exfiltration Chain Detected. "
                f"Outbound transfer to '{current_action.get('target')}' directly following access to sensitive resource '{sensitive_reads[0].get('target')}'. Blocked."
            )

    # Standalone suspicious transfer to known exfiltration endpoint
    elif is_transfer and transfer_type in ("KNOWN_EXFIL_ENDPOINT", "RAW_IP_ENDPOINT"):
        exfil_detected = True
        severity = "CRITICAL"
        decision = "BLOCK"
        reason = f"Attempted data transfer to suspicious or untrusted exfiltration endpoint: {current_action.get('target')}."

    return {
        "exfiltrationDetected": exfil_detected,
        "chainLinks": chain_links,
        "linkCount": len(chain_links),
        "severity": severity,
        "decision": decision,
        "reason": reason,
        "sensitiveReads": [a.get("target") for a in sensitive_reads],
        "isOutboundTransfer": is_transfer
    }
