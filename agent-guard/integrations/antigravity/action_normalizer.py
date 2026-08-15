"""
Action Normalizer for Antigravity Hook Bridge.
"""

import re
from typing import Dict, Any


def normalize_antigravity_action(tool_call: Dict[str, Any], workspace_paths: list = None) -> Dict[str, Any]:
    """
    Normalize an incoming Antigravity tool call payload into Agent Guard's generic action schema.
    """
    tool_name = (tool_call.get("name") or "").strip()
    args = tool_call.get("args") or {}

    action_type = "GENERAL_ACTION"
    target = ""
    description = ""
    parameters = {}

    # File Writing
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

    # File Reading
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

    # File Deletion
    elif tool_name in ("delete_file", "remove_file", "rm"):
        action_type = "FILE_DELETE"
        target = args.get("TargetFile") or args.get("FilePath") or args.get("path") or ""
        description = f"Delete file {target}"

    # Command Execution
    elif tool_name in ("run_command", "execute_command", "bash", "shell", "exec"):
        action_type = "COMMAND_EXECUTION"
        cmd = args.get("CommandLine") or args.get("command") or ""
        target = cmd
        description = args.get("description") or f"Execute shell command: {cmd}"

        cmd_lower = cmd.lower()
        if any(del_kw in cmd_lower for del_kw in ("rm -rf", "rmdir", "del /f", "drop database", "delete from")):
            action_type = "FILE_DELETE"
        elif any(sec_kw in cmd_lower for sec_kw in ("cat .env", "type .env", "printenv", "echo $api_key")):
            action_type = "SECRET_ACCESS"

    # Browser Automation
    elif tool_name in ("browser_subagent", "browser_task"):
        task_desc = args.get("Task") or args.get("TaskSummary") or args.get("TaskName") or ""
        target = args.get("TaskName") or "Browser Task"
        description = task_desc

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

    else:
        action_type = "MCP_TOOL_CALL" if "mcp" in tool_name.lower() else "GENERAL_ACTION"
        target = str(args)[:100]
        description = f"Invoke tool {tool_name}"

    target_clean = clean_target_path(target, workspace_paths)

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
    """Normalize file paths by stripping leading workspace prefixes."""
    if not target or not isinstance(target, str):
        return ""

    target_norm = target.replace("\\", "/")

    if workspace_paths:
        for ws in workspace_paths:
            ws_norm = ws.replace("\\", "/").rstrip("/")
            if target_norm.lower().startswith(ws_norm.lower()):
                target_norm = target_norm[len(ws_norm):].lstrip("/")
                break

    if re.match(r"^[a-zA-Z]:/", target_norm):
        parts = target_norm.split("/")
        if "safeai" in parts:
            idx = parts.index("safeai")
            target_norm = "/".join(parts[idx + 1:])

    return target_norm.lstrip("/") or target_norm
