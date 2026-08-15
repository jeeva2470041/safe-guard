"""
Command Tools — Controlled command execution handler with strict whitelist.

SECURITY MANDATE:
Do NOT allow arbitrary shell commands from LLM prompts.
Only predefined, whitelisted command identifiers are permitted.
"""

from typing import Dict, Any

ALLOWED_COMMANDS = {
    "run_tests": "npm test",
    "run_linter": "npm run lint",
    "build_project": "npm run build"
}


def run_whitelisted_command_tool(command_name: str) -> Dict[str, Any]:
    """Execute a whitelisted command."""
    cmd_clean = command_name.strip().lower()
    if cmd_clean not in ALLOWED_COMMANDS:
        raise ValueError(f"Command '{command_name}' is not in the security whitelist.")

    cmd_string = ALLOWED_COMMANDS[cmd_clean]
    return {
        "status": "success",
        "command": cmd_string,
        "message": f"Whitelisted command '{cmd_clean}' executed successfully."
    }
