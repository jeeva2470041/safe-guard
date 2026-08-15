"""
Action Normalizer Service — Converts Antigravity-specific tool calls into Agent Guard generic actions.

Generic Action Types:
- FILE_READ
- FILE_WRITE
- FILE_DELETE
- COMMAND_EXECUTION
- BROWSER_NAVIGATE
- BROWSER_CLICK
- BROWSER_TYPE
- BROWSER_SEARCH
- API_REQUEST
- MCP_TOOL_CALL
- EXTERNAL_TRANSACTION
- SECRET_ACCESS
- GENERAL_ACTION
"""

import os
import re
from typing import Dict, Any, Tuple


def normalize_antigravity_action(tool_call: Dict[str, Any], workspace_paths: list = None) -> Dict[str, Any]:
    """
    Normalize an incoming Antigravity tool call payload into Agent Guard's generic action schema.

    Antigravity tool calls typically take the form:
    {
      "name": "write_to_file",
      "args": {
        "TargetFile": "/path/to/file",
        "CodeContent": "..."
      }
    }
    """
    tool_name = (tool_call.get("name") or "").strip()
    args = tool_call.get("args") or {}

    # Extract target, action_type, description, parameters
    action_type = "GENERAL_ACTION"
    target = ""
    description = ""
    parameters = {}

    # 1. File Writing Tools
    if tool_name in ("write_to_file", "create_file", "save_file"):
        action_type = "FILE_WRITE"
        target = args.get("TargetFile") or args.get("FilePath") or args.get("path") or ""
        description = args.get("Description") or f"Write file {target}"
        parameters = {"code_length": len(args.get("CodeContent", ""))}

    elif tool_name in ("replace_file_content", "multi_replace_file_content", "edit_file", "patch_file"):
        action_type = "FILE_WRITE"
        target = args.get("TargetFile") or args.get("FilePath") or args.get("path") or ""
        description = args.get("Description") or args.get("Instruction") or f"Edit file {target}"
        parameters = {"instruction": args.get("Instruction", "")}

    # 2. File Reading Tools
    elif tool_name in ("view_file", "read_file", "cat_file", "read_file_content"):
        action_type = "FILE_READ"
        target = args.get("AbsolutePath") or args.get("FilePath") or args.get("path") or ""
        description = f"Read contents of {target}"

    elif tool_name in ("list_dir", "list_directory", "ls"):
        action_type = "FILE_READ"
        target = args.get("DirectoryPath") or args.get("path") or "."
        description = f"List directory contents of {target}"

    elif tool_name in ("grep_search", "find_in_files", "search_files"):
        action_type = "FILE_READ"
        target = args.get("SearchPath") or args.get("path") or "."
        description = f"Grep pattern '{args.get('Query', '')}' in {target}"

    # 3. File Deletion Tools
    elif tool_name in ("delete_file", "remove_file", "rm"):
        action_type = "FILE_DELETE"
        target = args.get("TargetFile") or args.get("FilePath") or args.get("path") or ""
        description = f"Delete file {target}"

    # 4. Command Execution
    elif tool_name in ("run_command", "execute_command", "bash", "shell", "exec"):
        action_type = "COMMAND_EXECUTION"
        cmd = args.get("CommandLine") or args.get("command") or ""
        target = cmd
        description = args.get("description") or f"Execute shell command: {cmd}"

        # Detect dangerous subcommands inside shell execution
        cmd_lower = cmd.lower()
        if any(del_kw in cmd_lower for del_kw in ("rm -rf", "rmdir", "del /f", "drop database", "delete from")):
            action_type = "FILE_DELETE"
        elif any(sec_kw in cmd_lower for sec_kw in ("cat .env", "type .env", "printenv", "echo $api_key")):
            action_type = "SECRET_ACCESS"

    # 5. Browser Automation Tools
    elif tool_name in ("browser_subagent", "browser_task"):
        task_desc = args.get("Task") or args.get("TaskSummary") or args.get("TaskName") or ""
        target = args.get("TaskName") or "Browser Task"
        description = task_desc

        # Classify browser sub-intent
        task_lower = task_desc.lower()
        if any(buy_kw in task_lower for buy_kw in ("pay", "purchase", "checkout", "book", "buy", "order", "charge", "₹", "$", "rs.")):
            action_type = "EXTERNAL_TRANSACTION"
        elif any(nav_kw in task_lower for nav_kw in ("navigate", "goto", "open url", "http", "www")):
            action_type = "BROWSER_NAVIGATE"
        else:
            action_type = "BROWSER_SEARCH"

    elif tool_name in ("read_url_content", "fetch_url"):
        action_type = "API_REQUEST"
        target = args.get("Url") or args.get("url") or ""
        description = f"Fetch HTTP content from {target}"

    elif tool_name in ("search_web", "web_search"):
        action_type = "BROWSER_SEARCH"
        target = args.get("query") or ""
        description = f"Web search query: {target}"

    # 6. Fallback General Tool Call
    else:
        action_type = "MCP_TOOL_CALL" if "mcp" in tool_name.lower() else "GENERAL_ACTION"
        target = str(args)[:100]
        description = f"Invoke tool {tool_name}"

    # Relativize target paths if workspace root is known
    target_clean = clean_target_path(target, workspace_paths)

    # Check for secret access in target
    if any(secret_file in target_clean.lower() for secret_file in (".env", "id_rsa", "id_ed25519", "credentials", "secrets.json")):
        action_type = "SECRET_ACCESS"

    return {
        "agent": "antigravity",
        "rawToolName": tool_name,
        "actionType": action_type,
        "target": target_clean,
        "description": description or f"{action_type} on {target_clean}",
        "rawArguments": args,
        "parameters": parameters,
    }


def clean_target_path(target: str, workspace_paths: list = None) -> str:
    """Normalize file paths by stripping leading workspace prefixes and converting to unix style."""
    if not target or not isinstance(target, str):
        return ""

    target_norm = target.replace("\\", "/")

    if workspace_paths:
        for ws in workspace_paths:
            ws_norm = ws.replace("\\", "/").rstrip("/")
            if target_norm.lower().startswith(ws_norm.lower()):
                target_norm = target_norm[len(ws_norm):].lstrip("/")
                break

    # Strip drive letter on Windows if present
    if re.match(r"^[a-zA-Z]:/", target_norm):
        parts = target_norm.split("/")
        # Keep relative path after workspace if recognizable
        if "safeai" in parts:
            idx = parts.index("safeai")
            target_norm = "/".join(parts[idx + 1:])

    return target_norm.lstrip("/") or target_norm
