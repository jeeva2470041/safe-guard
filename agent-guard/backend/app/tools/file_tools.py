"""
File Tools — Controlled file system handlers restricted strictly to backend/sandbox/.
"""

import os
from pathlib import Path
from typing import Dict, Any

# Root path of the safe sandbox
SANDBOX_DIR = Path(__file__).resolve().parent.parent.parent / "sandbox"


def resolve_sandbox_path(target: str) -> Path:
    """
    Resolve and validate path within sandbox.
    Raises ValueError on path traversal attempts or paths outside sandbox.
    """
    if not target or not isinstance(target, str):
        raise ValueError("Invalid target filename.")

    # Remove leading slashes/backslashes
    clean_target = target.lstrip("/\\")

    # Reject path traversal tokens or drive letters
    if ".." in clean_target or ":" in clean_target or clean_target.startswith("/") or clean_target.startswith("\\"):
        raise ValueError(f"Path traversal detected: '{target}' is outside permitted sandbox.")

    resolved = (SANDBOX_DIR / clean_target).resolve()

    # Ensure resolved path is inside SANDBOX_DIR
    try:
        resolved.relative_to(SANDBOX_DIR.resolve())
    except ValueError:
        raise ValueError(f"Target '{target}' resolves outside the permitted sandbox directory.")

    return resolved


def read_file_tool(target: str) -> Dict[str, Any]:
    """Read a permitted project file from sandbox."""
    file_path = resolve_sandbox_path(target)
    if not file_path.exists():
        return {
            "status": "error",
            "message": f"File '{target}' does not exist in sandbox.",
            "content": ""
        }

    content = file_path.read_text(encoding="utf-8")
    return {
        "status": "success",
        "target": target,
        "content": content[:1000],  # Truncate for safety
        "message": f"Successfully read {len(content)} bytes from '{target}'."
    }


def modify_file_tool(target: str, description: str = "") -> Dict[str, Any]:
    """Modify a permitted project file in sandbox."""
    file_path = resolve_sandbox_path(target)

    # Append modification note to prove execution occurred
    addition = f"\n// [Agent Guard Verified Update] {description}\n"
    if file_path.exists():
        current = file_path.read_text(encoding="utf-8")
        file_path.write_text(current + addition, encoding="utf-8")
    else:
        file_path.write_text(f"// New file created by agent: {description}\n", encoding="utf-8")

    return {
        "status": "success",
        "target": target,
        "message": f"Applied changes to '{target}' in sandbox."
    }


def modify_package_tool(target: str = "package.json", description: str = "") -> Dict[str, Any]:
    """Modify package configuration file in sandbox."""
    file_path = resolve_sandbox_path("package.json")
    if file_path.exists():
        addition = f"\n  // Update: {description}\n"
        file_path.write_text(file_path.read_text(encoding="utf-8") + addition, encoding="utf-8")

    return {
        "status": "success",
        "target": "package.json",
        "message": "Updated package.json dependencies in sandbox."
    }


def delete_file_tool(target: str) -> Dict[str, Any]:
    """
    Delete a file from sandbox.
    CRITICAL: This function is ONLY called if Security Gateway authorizes execution.
    """
    file_path = resolve_sandbox_path(target)
    if file_path.exists():
        file_path.unlink()
        return {
            "status": "success",
            "target": target,
            "message": f"File '{target}' deleted from sandbox."
        }
    return {
        "status": "notice",
        "target": target,
        "message": f"File '{target}' was already absent."
    }


def access_secret_tool(target: str = ".env") -> Dict[str, Any]:
    """Simulate secret file access in sandbox."""
    file_path = resolve_sandbox_path(target)
    if file_path.exists():
        return {
            "status": "success",
            "target": target,
            "message": f"Accessed secret file '{target}'."
        }
    return {
        "status": "notice",
        "target": target,
        "message": f"Secret target '{target}' accessed in sandbox."
    }
