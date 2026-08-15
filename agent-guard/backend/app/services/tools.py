"""
Tools Engine — Simulated execution handlers for agent actions.

HACKATHON SAFETY REQUIREMENT:
All tools are SIMULATED and perform NO real destructive file system or system operations.
"""

from typing import Dict, Any

AVAILABLE_TOOLS = [
    {
        "name": "read_file",
        "description": "Read contents of a source file",
        "parameters": {"target": "filename or file path"}
    },
    {
        "name": "modify_file",
        "description": "Modify contents of a source file",
        "parameters": {"target": "filename or file path", "description": "details of change"}
    },
    {
        "name": "run_tests",
        "description": "Run automated test suite",
        "parameters": {"target": "test file or package"}
    },
    {
        "name": "write_file",
        "description": "Write a new file to the workspace",
        "parameters": {"target": "filename or file path", "description": "file content or description"}
    },
    {
        "name": "modify_package_json",
        "description": "Modify package dependencies or scripts in package.json",
        "parameters": {"target": "package.json", "description": "dependency changes"}
    },
    {
        "name": "delete_file",
        "description": "Delete a file from the workspace",
        "parameters": {"target": "filename or file path"}
    },
    {
        "name": "access_env",
        "description": "Access environment secrets or .env file",
        "parameters": {"target": ".env or secret key name"}
    }
]


def execute_simulated_tool(action_type: str, target: str, description: str = "") -> Dict[str, Any]:
    """
    Execute a tool in simulation mode.

    Returns structured output indicating execution status without performing
    actual disk or database modifications.
    """
    action_upper = action_type.upper().strip()

    if action_upper == "READ_FILE":
        return {
            "execution": "SIMULATED",
            "action": "READ_FILE",
            "target": target,
            "status": "success",
            "message": f"Successfully read file content of '{target}' (simulated)."
        }
    elif action_upper == "MODIFY_FILE":
        return {
            "execution": "SIMULATED",
            "action": "MODIFY_FILE",
            "target": target,
            "status": "success",
            "message": f"Applied changes to '{target}' (simulated)."
        }
    elif action_upper == "RUN_TESTS":
        return {
            "execution": "SIMULATED",
            "action": "RUN_TESTS",
            "target": target,
            "status": "success",
            "message": f"Test suite '{target}' completed with 0 failures (simulated)."
        }
    elif action_upper == "WRITE_FILE":
        return {
            "execution": "SIMULATED",
            "action": "WRITE_FILE",
            "target": target,
            "status": "success",
            "message": f"Created new file '{target}' (simulated)."
        }
    elif action_upper in ("MODIFY_PACKAGE_JSON", "MODIFY_PACKAGE"):
        return {
            "execution": "SIMULATED",
            "action": "MODIFY_PACKAGE_JSON",
            "target": "package.json",
            "status": "success",
            "message": "Updated package.json dependencies (simulated)."
        }
    elif action_upper == "DELETE_FILE":
        return {
            "execution": "SIMULATED",
            "action": "DELETE_FILE",
            "target": target,
            "status": "simulated_delete",
            "message": f"Simulated deletion of '{target}' (no actual file removed)."
        }
    elif action_upper in ("ACCESS_ENV", "ACCESS_FILE"):
        return {
            "execution": "SIMULATED",
            "action": "ACCESS_ENV",
            "target": target,
            "status": "accessed",
            "message": f"Accessed environment context for '{target}' (simulated)."
        }
    else:
        return {
            "execution": "SIMULATED",
            "action": action_upper,
            "target": target,
            "status": "success",
            "message": f"Executed action '{action_upper}' on '{target}' (simulated)."
        }
