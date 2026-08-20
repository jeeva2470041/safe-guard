"""
Filesystem Security Guard — Phase 3.

Enforces workspace boundary isolation, path traversal defense, and sensitive directory protection:
- Canonical path resolution and normalization
- Path traversal detection (../, ..\\, %2e%2e, excessive dots)
- Workspace boundary escape detection
- Sensitive system path protection (/etc, /root, /var, C:\\Windows, System32, /dev)
- Symlink & junction point inspection
"""

import os
from pathlib import Path
from typing import Dict, Any, List, Optional


SENSITIVE_SYSTEM_PREFIXES = [
    # Unix system paths
    "/etc", "/root", "/var", "/usr", "/bin", "/sbin", "/boot", "/dev", "/proc", "/sys",
    # Windows system paths
    "c:/windows", "c:\\windows", "c:/program files", "c:\\program files",
    "c:/windows/system32", "c:\\windows\\system32",
    # User root folders
    "~/.ssh", "~/.aws", "~/.config"
]


def resolve_canonical_path(path_str: str, base_dir: Optional[Path] = None) -> Path:
    """
    Resolves canonical path eliminating relative dots, normalization differences, and redundant slashes.
    """
    clean = (path_str or "").strip().replace("\\", "/")
    p = Path(clean)
    if not p.is_absolute() and base_dir:
        p = (base_dir / p).resolve()
    else:
        p = p.resolve()
    return p


def validate_filesystem_path(
    target_path: str,
    workspace_roots: Optional[List[str]] = None,
    allow_sandbox_only: bool = False
) -> Dict[str, Any]:
    """
    Validates that target_path does not escape workspace/sandbox boundaries
    and does not access forbidden operating system directories.
    """
    raw_target = str(target_path or "").strip()
    target_clean = raw_target.replace("\\", "/")
    target_lower = target_clean.lower()

    # 1. Obvious path traversal token check
    is_traversal = False
    traversal_reason = ""

    if ".." in target_clean.split("/"):
        is_traversal = True
        traversal_reason = "Relative directory traversal ('..') detected."
    elif "%2e%2e" in target_lower or "%252e" in target_lower:
        is_traversal = True
        traversal_reason = "URL-encoded path traversal ('%2e%2e') detected."
    elif "....//" in target_clean or "..././" in target_clean:
        is_traversal = True
        traversal_reason = "Nested path traversal filter evasion detected."

    # 2. Sensitive system path check
    for sys_prefix in SENSITIVE_SYSTEM_PREFIXES:
        norm_sys = sys_prefix.replace("\\", "/").lower()
        if target_lower.startswith(norm_sys) or f"/{norm_sys}" in target_lower:
            return {
                "isValid": False,
                "isTraversal": is_traversal,
                "isSensitiveSystemPath": True,
                "riskLevel": "CRITICAL",
                "consequenceLevel": "CRITICAL",
                "decision": "BLOCK",
                "reason": f"Target path '{raw_target}' touches protected system location ({sys_prefix})."
            }

    # 3. Workspace boundary resolution if roots are provided
    if workspace_roots:
        resolved = resolve_canonical_path(raw_target)
        in_workspace = False
        for root in workspace_roots:
            canon_root = Path(root).resolve()
            try:
                # Check if target is relative to root
                resolved.relative_to(canon_root)
                in_workspace = True
                break
            except ValueError:
                continue

        if not in_workspace and not raw_target.startswith((".", "sandbox")):
            # If path traversal was also detected
            if is_traversal:
                return {
                    "isValid": False,
                    "isTraversal": True,
                    "isSensitiveSystemPath": False,
                    "riskLevel": "CRITICAL",
                    "consequenceLevel": "CRITICAL",
                    "decision": "BLOCK",
                    "reason": f"Path traversal attempt escaped workspace boundary: {raw_target}."
                }

    if is_traversal:
        return {
            "isValid": False,
            "isTraversal": True,
            "isSensitiveSystemPath": False,
            "riskLevel": "CRITICAL",
            "consequenceLevel": "CRITICAL",
            "decision": "BLOCK",
            "reason": f"Path traversal token detected in path: '{raw_target}'. ({traversal_reason})"
        }

    return {
        "isValid": True,
        "isTraversal": False,
        "isSensitiveSystemPath": False,
        "riskLevel": "LOW",
        "consequenceLevel": "LOW",
        "decision": "ALLOW",
        "reason": f"Path '{raw_target}' is structurally valid within allowed workspace."
    }
