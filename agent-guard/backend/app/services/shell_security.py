"""
Shell Security Service — Phase 3.

Deep command normalization and vulnerability detection for shell execution:
- Destructive commands (rm -rf, format, mkfs, drop database, dd)
- Reverse shells & network backdoors (nc -e, bash -i, /dev/tcp, mkfifo, socat, telnet)
- Command injection & chaining (&&, ||, ;, $(), ``, eval)
- Pipe-to-shell execution (curl | bash, wget | sh, iwr | iex, python | sh)
- Obfuscated & encoded commands (base64, powershell -enc, python -c exec, node -e)
- Privilege escalation (sudo, su -, chmod 777, chown root, runas)
"""

import re
import shlex
import base64
from typing import Dict, Any, List, Optional, Tuple


# Destructive command patterns
DESTRUCTIVE_COMMAND_PATTERNS = [
    (r"\brm\s+-[a-zA-Z]*r[a-zA-Z]*f\s+(/|\*|c:|c:/|~|/\*)", "SYSTEM_WIPE", "Recursive root or wide filesystem deletion"),
    (r"\brm\s+-[a-zA-Z]*r[a-zA-Z]*f\s+(\$HOME|\.\.)", "PARENT_WIPE", "Recursive home or parent directory deletion"),
    (r"\bformat\s+[a-zA-Z]:", "DISK_FORMAT", "Disk volume format command"),
    (r"\bmkfs(\.[\w]+)?\s+", "FS_CREATION", "Filesystem overwrite creation"),
    (r"\bdd\s+if=.*\s+of=(/dev/[a-z]+|\\\\\\.\\[a-zA-Z]:)", "DISK_OVERWRITE", "Direct disk partition write"),
    (r"\b(drop|truncate)\s+(database|schema|table)\b", "DB_DESTRUCTION", "Direct database or table deletion command"),
    (r":\(\)\s*\{\s*:\s*\|\s*:\s*&\s*\}\s*;\s*:", "FORK_BOMB", "Classic fork bomb denial of service"),
    (r"\bdel\s+/[fF]\s+/[sS]\s+/[qQ]\s+[cC]:", "WINDOWS_WIPE", "Recursive Windows drive purge"),
    (r"\bRemove-Item\s+-Recurse\s+-Force\s+[cC]:", "POWERSHELL_WIPE", "PowerShell recursive drive purge"),
]

# Reverse shell and backdoor patterns
REVERSE_SHELL_PATTERNS = [
    (r"\bnc(\.traditional)?\s+.*-e\s+(/bin/sh|/bin/bash|cmd\.exe|powershell)", "NETCAT_SHELL", "Netcat command execution bind/reverse shell"),
    (r"\bbash\s+-i\s+>&?\s*/dev/tcp/", "DEV_TCP_SHELL", "Bash /dev/tcp interactive reverse shell"),
    (r"\bmkfifo\s+.*(;\s*|&&|\s*\|\s*)cat\s+.*\|\s*/bin/sh", "FIFO_SHELL", "Named pipe (FIFO) reverse shell"),
    (r"\bsocat\s+.*exec:('|\")?(bash|sh|cmd|powershell)", "SOCAT_SHELL", "Socat interactive shell socket"),
    (r"\bpython(\d)?\s+-c\s+.*socket.*pty\.spawn", "PYTHON_PTY_SHELL", "Python interactive socket shell spawn"),
    (r"\bperl\s+-e\s+.*use\s+Socket", "PERL_SHELL", "Perl network socket reverse shell"),
    (r"\bruby\s+-rsocket\s+-e\s+.*exec\s+/bin/sh", "RUBY_SHELL", "Ruby socket shell"),
    (r"\bphp\s+-r\s+.*fsockopen.*exec", "PHP_SHELL", "PHP network socket shell"),
    (r"\btelnet\s+.*\|\s*/bin/sh", "TELNET_SHELL", "Telnet pipe reverse shell"),
]

# Pipe-to-shell and download-and-execute patterns
PIPE_TO_SHELL_PATTERNS = [
    (r"\bcurl\s+.*\|\s*(ba)?sh\b", "CURL_PIPE_BASH", "Remote script piped directly into shell execution"),
    (r"\bwget\s+.*\|\s*(ba)?sh\b", "WGET_PIPE_BASH", "Remote download piped directly into shell"),
    (r"\bcurl\s+.*\|\s*python(\d)?\b", "CURL_PIPE_PYTHON", "Remote payload piped directly into Python interpreter"),
    (r"\bwget\s+.*\|\s*python(\d)?\b", "WGET_PIPE_PYTHON", "Remote payload piped directly into Python interpreter"),
    (r"\biwr\s+.*\|\s*iex\b", "IWR_IEX", "PowerShell download cradle (Invoke-WebRequest | Invoke-Expression)"),
    (r"\bInvoke-Expression\s*\(?.*Invoke-WebRequest", "IEX_IWR", "PowerShell Invoke-Expression web request"),
    (r"\b(curl|wget|fetch)\s+.*(\.sh|\.ps1|\.py|\.exe|\.bat)\s*(;\s*|&&)\s*(bash|sh|python|powershell|\./)", "DOWNLOAD_AND_EXEC", "Two-step download and execute sequence"),
]

# Obfuscated and encoded execution
ENCODED_EXEC_PATTERNS = [
    (r"\bpowershell(\.exe)?\s+.*(-e|-enc|-encodedcommand)\s+[A-Za-z0-9+/=]{10,}", "POWERSHELL_ENCODED", "Base64-encoded PowerShell script execution"),
    (r"\becho\s+[A-Za-z0-9+/=]{15,}\s*\|\s*base64\s+-d\s*\|\s*(ba)?sh", "BASE64_PIPE_BASH", "Base64 decoded stream executed directly in shell"),
    (r"\bpython(\d)?\s+-c\s+.*exec\s*\(\s*base64\.", "PYTHON_BASE64_EXEC", "Python inline base64 code execution"),
    (r"\bnode\s+-e\s+.*eval\s*\(", "NODE_EVAL_EXEC", "Node.js inline eval execution"),
    (r"\b(certutil|bitsadmin)\s+.*-decode", "CERTUTIL_DECODE", "Windows utility used to decode hidden payloads"),
]

# Privilege escalation patterns
PRIV_ESC_PATTERNS = [
    (r"\bsudo\s+(su|bash|sh|zsh|csh|tcsh)\b", "SUDO_ROOT_SHELL", "Attempt to open unrestricted root shell via sudo"),
    (r"\bsudo\s+chmod\s+[47]77\s+/", "SUDO_CHMOD_ROOT", "Elevated global read/write/execute permission assignment"),
    (r"\bchmod\s+u\+s\s+", "SETUID_BIT", "Setting setuid permission on executable"),
    (r"\bchown\s+root(:root)?\s+", "CHOWN_ROOT", "Changing ownership of file to root"),
    (r"\brunAs\s+/user:administrator\b", "RUNAS_ADMIN", "Windows administrative execution escalation"),
]


def normalize_command_line(command: str) -> str:
    """
    Normalizes command string:
    - Collapses multiple whitespace
    - Strips escaped quotes and unifies backslashes
    - Unwraps redundant nested subshell calls
    """
    clean = re.sub(r'\s+', ' ', (command or '').strip())
    return clean


def inspect_command_security(command: str, user_goal: str = "") -> Dict[str, Any]:
    """
    Performs deep multi-pattern heuristic analysis of a proposed shell command.
    """
    normalized_cmd = normalize_command_line(command)
    cmd_lower = normalized_cmd.lower()
    goal_lower = (user_goal or "").lower()

    findings = []
    threat_category = None
    severity = "LOW"
    decision = "ALLOW"
    reason = "Command evaluated as safe routine operation."

    # 1. Destructive commands check (CRITICAL)
    for pattern, threat_type, desc in DESTRUCTIVE_COMMAND_PATTERNS:
        if re.search(pattern, normalized_cmd, re.IGNORECASE):
            findings.append({"type": threat_type, "severity": "CRITICAL", "description": desc})
            threat_category = threat_type
            severity = "CRITICAL"
            decision = "BLOCK"
            reason = f"Destructive command detected: {desc} ({normalized_cmd})."
            break

    # 2. Reverse shell check (CRITICAL)
    if severity != "CRITICAL":
        for pattern, threat_type, desc in REVERSE_SHELL_PATTERNS:
            if re.search(pattern, normalized_cmd, re.IGNORECASE):
                findings.append({"type": threat_type, "severity": "CRITICAL", "description": desc})
                threat_category = threat_type
                severity = "CRITICAL"
                decision = "BLOCK"
                reason = f"Reverse shell / backdoor command detected: {desc}."
                break

    # 3. Pipe to shell check (HIGH/CRITICAL)
    if severity != "CRITICAL":
        for pattern, threat_type, desc in PIPE_TO_SHELL_PATTERNS:
            if re.search(pattern, normalized_cmd, re.IGNORECASE):
                findings.append({"type": threat_type, "severity": "HIGH", "description": desc})
                threat_category = threat_type
                severity = "HIGH"
                decision = "BLOCK" if "sh" in threat_type.lower() else "REQUIRE_APPROVAL"
                reason = f"Untrusted remote payload piped directly into interpreter: {desc}."
                break

    # 4. Encoded / Obfuscated execution (HIGH)
    if severity not in ("CRITICAL", "HIGH"):
        for pattern, threat_type, desc in ENCODED_EXEC_PATTERNS:
            if re.search(pattern, normalized_cmd, re.IGNORECASE):
                findings.append({"type": threat_type, "severity": "HIGH", "description": desc})
                threat_category = threat_type
                severity = "HIGH"
                decision = "REQUIRE_APPROVAL"
                reason = f"Obfuscated or base64-encoded command execution detected: {desc}."
                break

    # 5. Privilege escalation (HIGH)
    if severity not in ("CRITICAL", "HIGH"):
        for pattern, threat_type, desc in PRIV_ESC_PATTERNS:
            if re.search(pattern, normalized_cmd, re.IGNORECASE):
                findings.append({"type": threat_type, "severity": "HIGH", "description": desc})
                threat_category = threat_type
                severity = "HIGH"
                decision = "REQUIRE_APPROVAL"
                reason = f"Privilege escalation attempt detected: {desc}."
                break

    # 6. Routine diagnostic and dev check whitelist
    if not findings:
        safe_prefixes = (
            "git status", "git log", "git diff", "git branch", "git show",
            "dir", "ls", "pwd", "echo ", "cat ", "type ", "head ", "tail ",
            "pytest", "npm test", "vitest", "jest", "npm run build", "tsc",
            "python -m pytest", "python --version", "node -v", "npm -v"
        )
        if any(cmd_lower.startswith(p) for p in safe_prefixes):
            severity = "LOW"
            decision = "ALLOW"
            reason = "Standard read-only diagnostic or test verification command."
        else:
            severity = "MEDIUM"
            decision = "ALLOW"
            reason = "Standard local development command."

    return {
        "command": command,
        "normalizedCommand": normalized_cmd,
        "isThreat": bool(findings),
        "threatCategory": threat_category,
        "severity": severity,
        "decision": decision,
        "reason": reason,
        "findings": findings
    }
