"""
Tool Registry — Central controlled tool registry.

CRITICAL CONTROL ENFORCEMENT:
The agent MUST NOT receive direct Python function references.
Execution path MUST always be:
Agent Proposal → Security Gateway → Tool Registry → Tool Execution
"""

from typing import Dict, Any, Callable
from app.tools.file_tools import (
    read_file_tool,
    modify_file_tool,
    modify_package_tool,
    delete_file_tool,
    access_secret_tool,
)
from app.tools.test_tools import run_tests_tool
from app.tools.command_tools import run_whitelisted_command_tool


TOOLS_REGISTRY: Dict[str, Callable] = {
    "READ_FILE": read_file_tool,
    "read_file": read_file_tool,
    "MODIFY_FILE": modify_file_tool,
    "modify_file": modify_file_tool,
    "MODIFY_PACKAGE": modify_package_tool,
    "modify_package": modify_package_tool,
    "MODIFY_PACKAGE_JSON": modify_package_tool,
    "modify_package_json": modify_package_tool,
    "RUN_TESTS": run_tests_tool,
    "run_tests": run_tests_tool,
    "DELETE_FILE": delete_file_tool,
    "delete_file": delete_file_tool,
    "ACCESS_SECRET": access_secret_tool,
    "access_secret": access_secret_tool,
    "ACCESS_ENV": access_secret_tool,
    "access_env": access_secret_tool,
    "RUN_COMMAND": run_whitelisted_command_tool,
    "run_command": run_whitelisted_command_tool,
}


def dispatch_tool_execution(action_type: str, target: str, description: str = "") -> Dict[str, Any]:
    """
    Dispatch and execute a tool from the controlled registry.
    This function can ONLY be called by the Security Gateway after authorization.
    """
    action_key = action_type.strip()
    handler = TOOLS_REGISTRY.get(action_key) or TOOLS_REGISTRY.get(action_key.upper())

    if not handler:
        # Fallback to read_file_tool if unknown
        return read_file_tool(target)

    # Invoke appropriate tool based on parameter expectations
    if handler in (modify_file_tool, modify_package_tool):
        return handler(target, description)
    else:
        return handler(target)
