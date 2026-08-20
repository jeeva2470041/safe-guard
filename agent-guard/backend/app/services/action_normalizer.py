"""
Action Normalizer Service — Converts Antigravity-specific tool calls into Agent Guard generic actions.

Supports Phase 1 & Phase 2:
- Expanded Real-World Action Normalization (Browser, API, Email, Financial, Forms, MCP, File, Commands)
- Consequence Levels: LOW | MEDIUM | HIGH | CRITICAL
- Reversibility: REVERSIBLE | PARTIALLY_REVERSIBLE | IRREVERSIBLE
- Instruction Source Trust: USER | SYSTEM | AGENT_PLAN | TRUSTED_TOOL | WEBSITE | DOCUMENT | EMAIL | SEARCH_RESULT | API_RESPONSE | MCP_TOOL | UNKNOWN
"""

import os
import re
from typing import Dict, Any, Tuple, Optional


def classify_instruction_source(tool_call: Dict[str, Any], tool_name: str, args: Dict[str, Any]) -> str:
    """
    Classify the source trust of an instruction:
    USER | SYSTEM | AGENT_PLAN | TRUSTED_TOOL | WEBSITE | DOCUMENT | EMAIL | SEARCH_RESULT | API_RESPONSE | MCP_TOOL | UNKNOWN
    """
    explicit_source = tool_call.get("source") or args.get("source") or args.get("instruction_source")
    if explicit_source:
        source_upper = str(explicit_source).strip().upper()
        if source_upper in (
            "USER", "SYSTEM", "AGENT_PLAN", "TRUSTED_TOOL", "WEBSITE",
            "DOCUMENT", "EMAIL", "SEARCH_RESULT", "API_RESPONSE", "MCP_TOOL", "UNKNOWN"
        ):
            return source_upper

    name_lower = tool_name.lower()
    if "mcp" in name_lower or "mcp_" in name_lower:
        return "MCP_TOOL"
    elif "search_web" in name_lower or "web_search" in name_lower:
        return "SEARCH_RESULT"
    elif "read_url" in name_lower or "fetch_url" in name_lower:
        return "API_RESPONSE"
    elif "browser" in name_lower:
        task_desc = str(args.get("Task") or args.get("TaskSummary") or "").lower()
        if "email" in task_desc or "gmail" in task_desc or "inbox" in task_desc:
            return "EMAIL"
        elif "search" in task_desc:
            return "SEARCH_RESULT"
        return "WEBSITE"

    target_str = str(args.get("TargetFile") or args.get("AbsolutePath") or args.get("CommandLine") or "").lower()
    if any(doc_ext in target_str for doc_ext in (".pdf", ".docx", ".xlsx", ".csv", ".txt", ".md")) and "read" in name_lower:
        return "DOCUMENT"

    return "AGENT_PLAN"


def determine_action_consequence_and_reversibility(action_type: str, target: str, args: Dict[str, Any]) -> Tuple[str, str, str]:
    """
    Compute consequence explanation, consequence level, and reversibility rating.
    Returns: (consequence_description, consequence_level, reversibility)
    consequence_level: LOW | MEDIUM | HIGH | CRITICAL
    reversibility: REVERSIBLE | PARTIALLY_REVERSIBLE | IRREVERSIBLE
    """
    target_lower = target.lower()

    # ── CRITICAL ──
    if action_type == "SECRET_ACCESS" or any(s in target_lower for s in (".env", "id_rsa", "id_ed25519", "cookie", "shadow", "password", "api_key", "secret")):
        return ("Accesses confidential credentials, authentication cookies, API keys, or private system keys.", "CRITICAL", "IRREVERSIBLE")

    if action_type == "COMMAND_EXECUTION" and any(crit in target_lower for crit in ("rm -rf /", "drop database", "format ", "mkfs", "wipe", "dd if=")):
        return ("Catastrophic system or database destruction command.", "CRITICAL", "IRREVERSIBLE")

    # ── HIGH ──
    if action_type in ("FINANCIAL_INITIATE_PAYMENT", "FINANCIAL_CONFIRM_PAYMENT", "EXTERNAL_TRANSACTION"):
        return ("Initiates monetary charge, payment authorization, or non-refundable reservation.", "HIGH", "IRREVERSIBLE")

    if action_type in ("FILE_DELETE", "API_DELETE"):
        return (f"Permanently deletes data or remote resource '{target}'.", "HIGH", "IRREVERSIBLE")

    if action_type in ("BROWSER_UPLOAD", "MCP_RESOURCE_WRITE", "EXTERNAL_UPLOAD"):
        return (f"Uploads local or session data to external destination '{target}'.", "HIGH", "PARTIALLY_REVERSIBLE")

    # ── MEDIUM ──
    if action_type in ("EMAIL_SEND", "EXTERNAL_COMMUNICATION"):
        return (f"Transmits electronic message or email to external recipient '{target}'.", "MEDIUM", "IRREVERSIBLE")

    if action_type in ("FORM_SUBMIT", "BROWSER_SUBMIT"):
        return (f"Submits form data to target endpoint or web portal '{target}'.", "MEDIUM", "PARTIALLY_REVERSIBLE")

    if action_type in ("FILE_WRITE", "API_POST", "API_PUT", "API_PATCH"):
        if any(sens in target_lower for sens in ("package.json", "pom.xml", "settings.py", "dockerfile")):
            return ("Modifies project dependencies or configuration.", "MEDIUM", "PARTIALLY_REVERSIBLE")
        return (f"Modifies content of file or API resource '{target}'.", "MEDIUM", "PARTIALLY_REVERSIBLE")

    if action_type in ("BROWSER_CLICK", "MCP_INVOCATION", "FINANCIAL_SELECT_PAYMENT"):
        return (f"Interacts with interactive elements on '{target}'.", "MEDIUM", "REVERSIBLE")

    if action_type in ("BROWSER_DOWNLOAD", "EMAIL_ATTACH", "EMAIL_COMPOSE"):
        return (f"Stages document or content attachment for '{target}'.", "MEDIUM", "REVERSIBLE")

    # ── LOW ──
    if action_type in ("BROWSER_SEARCH", "BROWSER_NAVIGATE", "BROWSER_SELECT", "BROWSER_TYPE", "FORM_FILL", "BROWSER_READ_PAGE", "BROWSER_EXTRACT", "FINANCIAL_VIEW_PRICE", "FILE_READ", "API_GET", "MCP_DISCOVERY", "MCP_RESOURCE_READ", "EMAIL_READ"):
        return ("Read-only query, input typing, dropdown selection, or public information inspection.", "LOW", "REVERSIBLE")

    return ("General automated agent operation.", "LOW", "REVERSIBLE")


def clean_target_path(target: str, workspace_paths: list = None) -> str:
    """Clean and normalize target path relative to workspace."""
    clean = target.replace("\\", "/")
    if workspace_paths:
        for wp in workspace_paths:
            wp_clean = wp.replace("\\", "/")
            if clean.startswith(wp_clean):
                clean = clean[len(wp_clean):].lstrip("/")
    return clean


def normalize_antigravity_action(tool_call: Dict[str, Any], workspace_paths: list = None) -> Dict[str, Any]:
    """
    Normalize an incoming Antigravity tool call payload into Agent Guard's canonical action schema.
    Supports all Browser, API, Email, Financial, Form, MCP, File, and Command operations.
    """
    tool_name = (tool_call.get("name") or "").strip()
    args = tool_call.get("args") or {}

    action_type = "GENERAL_ACTION"
    target = ""
    description = ""
    purpose = tool_call.get("purpose") or args.get("purpose") or ""
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
        description = args.get("Instruction") or args.get("Description") or f"Edit file {target}"
        parameters = {"instruction": args.get("Instruction")}

    # 2. File Reading Tools
    elif tool_name in ("view_file", "read_file", "view_file_outline", "get_file"):
        action_type = "FILE_READ"
        target = args.get("AbsolutePath") or args.get("TargetFile") or args.get("FilePath") or args.get("path") or ""
        description = f"View contents of {target}"

    # 3. Directory & Search Tools
    elif tool_name in ("list_dir", "list_directory", "dir_list"):
        action_type = "FILE_READ"
        target = args.get("DirectoryPath") or args.get("path") or "."
        description = f"List directory contents of {target}"

    elif tool_name in ("grep_search", "find_in_files", "search_files"):
        action_type = "FILE_READ"
        target = args.get("SearchPath") or args.get("path") or "."
        query = args.get("Query", "")
        description = f"Search files in {target} for pattern '{query}'"
        parameters = {"query": query}

    # 4. Command Execution
    elif tool_name in ("run_command", "execute_command", "bash", "shell", "terminal"):
        action_type = "COMMAND_EXECUTION"
        cmd = args.get("CommandLine") or args.get("command") or ""
        target = cmd.strip()
        description = f"Execute shell command: {cmd}"
        parameters = {"cwd": args.get("Cwd", ""), "is_daemon": args.get("IsDaemon", False)}

    # 5. Web Search & Reading
    elif tool_name in ("search_web", "web_search", "google_search"):
        action_type = "BROWSER_SEARCH"
        target = args.get("query") or args.get("search_query") or ""
        description = f"Search the web for '{target}'"

    elif tool_name in ("read_url_content", "fetch_url", "http_get"):
        action_type = "BROWSER_NAVIGATE"
        target = args.get("Url") or args.get("url") or ""
        description = f"Fetch static web content from {target}"

    # 6. Browser Subagent & Real-World Browser Actions
    elif tool_name in ("browser_subagent", "browser_action", "puppet", "playwright"):
        task_name = args.get("TaskName", "")
        task_summary = args.get("TaskSummary", "")
        task_desc = args.get("Task", "")
        combined = f"{task_name} {task_summary} {task_desc}".lower()

        # Classify sub-browser action types
        if any(kw in combined for kw in ("book a flight", "flight purchase", "purchase chennai", "flight checkout", "purchase ticket")):
            action_type = "EXTERNAL_TRANSACTION"
            target = task_name or "Payment Gateway"
        elif any(kw in combined for kw in ("pay", "checkout", "cvv", "card payment", "authorize charge")):
            action_type = "FINANCIAL_INITIATE_PAYMENT"
            target = task_name or "Payment Gateway"
        elif any(kw in combined for kw in ("select payment", "choose payment", "credit card option")):
            action_type = "FINANCIAL_SELECT_PAYMENT"
            target = task_name or "Payment Method Selector"
        elif any(kw in combined for kw in ("price", "fare", "view tariff", "compare prices")):
            action_type = "FINANCIAL_VIEW_PRICE"
            target = task_name or "Pricing Table"
        elif any(kw in combined for kw in ("upload", "upload file", "upload cookies")):
            action_type = "BROWSER_UPLOAD"
            target = task_name or "File Upload Form"
        elif any(kw in combined for kw in ("download", "export pdf", "download ticket")):
            action_type = "BROWSER_DOWNLOAD"
            target = task_name or "Download Resource"
        elif any(kw in combined for kw in ("submit", "confirm booking", "submit form")):
            action_type = "BROWSER_SUBMIT"
            target = task_name or "Form Submit"
        elif any(kw in combined for kw in ("select", "dropdown", "seat")):
            action_type = "BROWSER_SELECT"
            target = task_name or "Seat / Option Selection"
        elif any(kw in combined for kw in ("fill", "type", "passenger", "name field", "address form")):
            action_type = "BROWSER_TYPE"
            target = task_name or "Form Input"
        elif any(kw in combined for kw in ("click", "choose flight", "pick room")):
            action_type = "BROWSER_CLICK"
            target = task_name or "Interactive Element"
        elif any(kw in combined for kw in ("extract", "scrape", "table data")):
            action_type = "BROWSER_EXTRACT"
            target = task_name or "Web Content"
        elif any(kw in combined for kw in ("navigate", "open url", "visit")):
            action_type = "BROWSER_NAVIGATE"
            target = task_name or "Target Web Page"
        else:
            action_type = "BROWSER_NAVIGATE"
            target = task_name or "Browser Action"

        description = task_summary or task_desc or f"Browser task: {task_name}"

    # 7. API Actions
    elif tool_name in ("api_call", "rest_api", "http_request"):
        method = str(args.get("method", "GET")).upper()
        target = args.get("endpoint") or args.get("url") or ""
        action_map = {
            "GET": "API_GET",
            "POST": "API_POST",
            "PUT": "API_PUT",
            "PATCH": "API_PATCH",
            "DELETE": "API_DELETE"
        }
        action_type = action_map.get(method, "API_POST")
        description = f"Execute HTTP {method} request to {target}"

    # 8. Email Actions
    elif tool_name in ("send_email", "compose_email", "mail_service"):
        if "compose" in tool_name or args.get("draft"):
            action_type = "EMAIL_COMPOSE"
        else:
            action_type = "EMAIL_SEND"
        target = args.get("to") or args.get("recipient") or "external_recipient"
        description = f"Email action to {target}: {args.get('subject', '')}"

    # 9. MCP Tools
    elif tool_name.startswith("mcp_") or "mcp" in tool_name:
        if "discover" in tool_name or "list" in tool_name:
            action_type = "MCP_DISCOVERY"
            target = args.get("server") or "MCP Server"
            description = "Discover available MCP tools and resources"
        elif "read" in tool_name:
            action_type = "MCP_RESOURCE_READ"
            target = args.get("uri") or args.get("resource") or "MCP Resource"
            description = f"Read MCP resource: {target}"
        elif "write" in tool_name:
            action_type = "MCP_RESOURCE_WRITE"
            target = args.get("uri") or args.get("resource") or "MCP Resource"
            description = f"Write MCP resource: {target}"
        else:
            action_type = "MCP_INVOCATION"
            target = args.get("tool") or tool_name
            description = f"Invoke MCP tool '{target}'"

    # 10. Direct / Passthrough Canonical Types
    elif tool_name.upper() in (
        "BROWSER_NAVIGATE", "BROWSER_CLICK", "BROWSER_TYPE", "BROWSER_SELECT", "BROWSER_SUBMIT",
        "BROWSER_DOWNLOAD", "BROWSER_UPLOAD", "BROWSER_READ_PAGE", "BROWSER_EXTRACT", "BROWSER_SEARCH",
        "API_GET", "API_POST", "API_PUT", "API_PATCH", "API_DELETE",
        "EMAIL_READ", "EMAIL_COMPOSE", "EMAIL_SEND", "EMAIL_ATTACH",
        "FINANCIAL_VIEW_PRICE", "FINANCIAL_SELECT_PAYMENT", "FINANCIAL_INITIATE_PAYMENT", "FINANCIAL_CONFIRM_PAYMENT",
        "FORM_FILL", "FORM_SUBMIT",
        "MCP_DISCOVERY", "MCP_INVOCATION", "MCP_RESOURCE_READ", "MCP_RESOURCE_WRITE",
        "FILE_READ", "FILE_WRITE", "FILE_DELETE", "COMMAND_EXECUTION", "SECRET_ACCESS", "EXTERNAL_TRANSACTION", "EXTERNAL_COMMUNICATION", "EXTERNAL_UPLOAD"
    ):
        action_type = tool_name.upper()
        target = args.get("target") or args.get("TargetFile") or args.get("destination") or ""
        description = args.get("description") or f"Action {action_type} on {target}"

    else:
        target = tool_name
        description = f"Execute tool: {tool_name}"

    # 11. Normalize & relativize targets
    target = clean_target_path(target, workspace_paths)

    # 12. Security Secret Override
    target_lower = target.lower()
    if any(secret_file in target_lower for secret_file in (".env", "id_rsa", "id_ed25519", "cookies.sqlite", "shadow", "credentials.json")):
        action_type = "SECRET_ACCESS"

    # 13. Source Trust, Consequence, and Reversibility
    source = classify_instruction_source(tool_call, tool_name, args)
    consequence_desc, consequence_level, reversibility = determine_action_consequence_and_reversibility(action_type, target, args)

    return {
        "actionType": action_type,
        "target": target,
        "description": description,
        "purpose": purpose or description,
        "source": source,
        "consequence": consequence_desc,
        "consequenceLevel": consequence_level,
        "reversibility": reversibility,
        "parameters": parameters,
        "rawToolName": tool_name,
        "agent": "antigravity"
    }
