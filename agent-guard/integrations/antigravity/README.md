# Google Antigravity Integration for Agent Guard

This module connects **Google Antigravity** directly to the **Agent Guard Security Gateway** using Antigravity's native `PreToolUse` lifecycle hook mechanism.

---

## 🎯 Architecture Flow

```text
Google Antigravity proposes Tool Call
                 ↓
      .agents/hooks.json (PreToolUse)
                 ↓
agent_guard_hook.py (stdin payload)
                 ↓ HTTP POST /api/agent/intercept
Agent Guard FastAPI Security Gateway
                 ↓
Action Normalization → Active Goal Policy → Multi-Step Drift → Risk Engine → Decision
                 ↓
Hook Response [stdout: {"decision": "allow" | "deny" | "ask", "reason": "..."}]
                 ↓
Google Antigravity
    ├── ALLOW → Tool executes
    ├── ASK   → Prompts user for confirmation
    └── DENY  → Hard block: Tool NEVER executes
```

---

## ⚙️ Configuration (`hooks.json`)

To enable the interceptor in Antigravity, add the following configuration to your workspace customization root (`.agents/hooks.json`):

```json
{
  "agent-guard-interceptor": {
    "enabled": true,
    "PreToolUse": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "python ./agent-guard/integrations/antigravity/agent_guard_hook.py",
            "timeout": 15
          }
        ]
      }
    ]
  }
}
```

---

## 📡 Payload Contract

### Input from Antigravity (stdin)
```json
{
  "toolCall": {
    "name": "write_to_file",
    "args": {
      "TargetFile": "backend/server.js",
      "CodeContent": "..."
    }
  },
  "stepIdx": 12,
  "conversationId": "c7867fff-ccc5-442c-aff8-f3cd9aa0a037",
  "workspacePaths": ["c:/Users/priya/jeeva_project/safeai"]
}
```

### Output to Antigravity (stdout)
```json
{
  "decision": "deny",
  "reason": "[Agent Guard] Action BLOCKED: Violates active goal constraint: Do not modify backend"
}
```
