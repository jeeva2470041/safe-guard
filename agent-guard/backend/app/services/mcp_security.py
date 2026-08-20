"""
MCP Security Service — Phase 3.

Evaluates Model Context Protocol (MCP) tool registrations and invocations for:
- Tool Poisoning: malicious or hidden prompt instructions embedded in tool descriptions
- Capability Mismatches: benign tool names (e.g. 'format_json') masking high-impact operations
- Unauthorized Resource Access: MCP resource reads/writes targeting sensitive or network paths
- Unknown Tool Policy: unvetted tools default to REQUIRE_APPROVAL (Fail-Closed)
"""

import re
from typing import Dict, Any, List, Optional
from app.services.prompt_injection_detector import detect_prompt_injection


KNOWN_SAFE_MCP_TOOLS = {
    "fetch_documentation", "query_database_readonly", "format_code",
    "calculate_math", "search_kb", "lookup_reference", "translate_text"
}

SUSPICIOUS_MCP_DESCRIPTION_PATTERNS = [
    (r"ignore\s+(previous|prior)\s+instructions?", "INSTRUCTION_OVERRIDE", "Tool description attempts to override agent instructions"),
    (r"(exfiltrate|upload|send|post)\s+.*(to|at)\s+https?://", "HIDDEN_EXFILTRATION", "Tool description instructs sending session data externally"),
    (r"(read|dump|extract)\s+.*(\.env|id_rsa|cookie|password|secret|credential)", "HIDDEN_SECRET_ACCESS", "Tool description secretly requests credentials or private keys"),
    (r"disable\s+(security|safeguard|guard)", "DISABLE_SECURITY", "Tool description instructs agent to turn off safeguards"),
    (r"\bsudo\s+", "PRIVILEGE_ESCALATION", "Tool description instructs elevated sudo execution"),
]


def inspect_mcp_tool_registration(
    tool_name: str,
    description: str,
    parameters_schema: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Inspects an MCP tool manifest for poisoning, prompt injection, or capability deception.
    """
    clean_name = str(tool_name or "").strip()
    clean_desc = str(description or "").strip()
    findings = []
    severity = "LOW"
    decision = "ALLOW"
    is_poisoned = False

    # 1. Scan description for embedded prompt injection
    injection_res = detect_prompt_injection(clean_desc, source="MCP_TOOL")
    if injection_res["detected"] and injection_res["severity"] in ("CRITICAL", "HIGH"):
        findings.append({
            "type": "PROMPT_INJECTION_IN_TOOL",
            "severity": injection_res["severity"],
            "description": f"MCP tool description contains prompt injection: {injection_res['injectionType']}"
        })
        is_poisoned = True
        severity = "CRITICAL"
        decision = "BLOCK"

    # 2. Check for suspicious imperative directive patterns in description
    if not is_poisoned:
        for pattern, threat_type, threat_desc in SUSPICIOUS_MCP_DESCRIPTION_PATTERNS:
            if re.search(pattern, clean_desc, re.IGNORECASE):
                findings.append({
                    "type": threat_type,
                    "severity": "CRITICAL" if "secret" in threat_type.lower() or "exfil" in threat_type.lower() else "HIGH",
                    "description": threat_desc
                })
                is_poisoned = True
                severity = "CRITICAL"
                decision = "BLOCK"
                break

    # 3. Check for capability mismatch (deceptive naming)
    # If name suggests read-only or formatting, but description contains write/delete/execute
    name_lower = clean_name.lower()
    desc_lower = clean_desc.lower()
    if any(safe in name_lower for safe in ("read", "get", "format", "view", "list", "check", "math", "calc")):
        if any(destructive in desc_lower for destructive in ("delete", "remove", "drop", "overwrite", "write file", "shell", "execute command")):
            findings.append({
                "type": "CAPABILITY_MISMATCH",
                "severity": "HIGH",
                "description": f"Tool '{clean_name}' suggests read-only operation, but description specifies destructive/modifying actions."
            })
            if severity != "CRITICAL":
                severity = "HIGH"
                decision = "REQUIRE_APPROVAL"

    # 4. Unknown tool check (Fail-closed policy)
    if not findings and clean_name not in KNOWN_SAFE_MCP_TOOLS:
        decision = "REQUIRE_APPROVAL"
        severity = "MEDIUM"
        findings.append({
            "type": "UNKNOWN_MCP_TOOL",
            "severity": "MEDIUM",
            "description": f"MCP tool '{clean_name}' is not in the verified whitelist; requiring human confirmation."
        })

    reason = "; ".join([f["description"] for f in findings]) if findings else f"MCP tool '{clean_name}' passed security inspection."

    return {
        "toolName": clean_name,
        "isPoisoned": is_poisoned,
        "severity": severity,
        "decision": decision,
        "reason": reason,
        "findings": findings
    }


def inspect_mcp_invocation(
    tool_name: str,
    arguments: Dict[str, Any],
    user_goal: str = ""
) -> Dict[str, Any]:
    """
    Inspects an active MCP tool call invocation for parameter anomalies or secret targets.
    """
    args_str = str(arguments).lower()
    findings = []
    severity = "LOW"
    decision = "ALLOW"

    # Check for sensitive paths in arguments
    if any(secret in args_str for secret in (".env", "id_rsa", "cookies.sqlite", "shadow", "credentials.json")):
        severity = "CRITICAL"
        decision = "BLOCK"
        findings.append({
            "type": "MCP_SECRET_ACCESS",
            "severity": "CRITICAL",
            "description": "MCP tool invocation contains sensitive credential or private key target in arguments."
        })

    # Check for shell command injection in arguments
    if any(cmd in args_str for cmd in ("rm -rf", "drop table", "nc -e", "bash -i")):
        severity = "CRITICAL"
        decision = "BLOCK"
        findings.append({
            "type": "MCP_COMMAND_INJECTION",
            "severity": "CRITICAL",
            "description": "MCP tool invocation contains destructive or reverse shell command in arguments."
        })

    reason = "; ".join([f["description"] for f in findings]) if findings else "MCP invocation arguments evaluated as safe."

    return {
        "toolName": tool_name,
        "isThreat": bool(findings),
        "severity": severity,
        "decision": decision,
        "reason": reason,
        "findings": findings
    }
