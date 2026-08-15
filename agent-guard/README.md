# Agent Guard — Runtime Goal Integrity & Action Authorization

> **A runtime security and authorization layer for autonomous AI agents.**
> 
> *"We do not merely evaluate individual AI actions. We continuously monitor whether the agent's behavior remains consistent with the user's original goal throughout execution."*

---

## 🌟 Overview

Autonomous AI coding agents can execute dozens of actions while pursuing a goal. Without runtime guardrails, agents frequently experience **goal drift**, modifying files outside their permitted scope, leaking secrets, or altering critical databases.

**Agent Guard** sits between the AI agent and its tool execution layer, intercepting every proposed action in real time. It evaluates actions against a dynamically generated **Goal Policy**, performs **multi-step drift analysis**, computes **cumulative risk**, and **automatically pauses or blocks** the agent before any unsafe operation can execute.

### Primary Integration: Google Antigravity

Agent Guard integrates with **Google Antigravity** through the native **PreToolUse** hook mechanism. Every tool action proposed by Antigravity is intercepted, normalized, evaluated against the active Goal Policy, and authorized or denied **before execution**.

> **Antigravity decides HOW to accomplish the user's goal. Agent Guard decides WHETHER each proposed action is authorized to execute.**

---

## 🛡️ Key Features & Capabilities

### 1. Dynamic Goal Analyzer & Policy Generation
- Users enter goals in natural language (e.g. *"Create a portfolio website using React with a dark theme. Do not modify the backend"*).
- The system dynamically synthesizes:
  - **Objective**: Target functional goal
  - **Domain Classification**: Frontend, Spring Boot, Python, Database, Document/PDF
  - **Allowed Scope**: Explicit components and directories permitted for modification
  - **Restricted Scope**: Boundaries strictly forbidden (e.g. backend servers, SQL schemas, secrets)
  - **User Constraints**: Enforced negative constraints
- OpenAI is used optionally for semantic policy generation; a deterministic rule-based fallback is included.

### 2. Multi-Step Goal Drift Detection (`goal_drift.py`)
- Tracks the **multi-step trajectory** of recent actions (3–5 actions) rather than evaluating actions in isolation.
- Detects gradual divergence when an agent transitions from allowed tasks into unauthorized services.
- **Drift Score (0–100)** mapped to standard levels:
  - `0–20`: **NORMAL**
  - `21–40`: **LOW**
  - `41–60`: **MODERATE**
  - `61–80`: **HIGH**
  - `81–100`: **CRITICAL**

### 3. Cumulative Risk Escalation (`risk_engine.py`)
- Session-wide risk tracking with exponential escalation penalties for repeated violations, high-risk actions, or credential touches.
- **Cumulative Risk Levels**: `LOW` (0–30), `MODERATE` (31–50), `HIGH` (51–70), `CRITICAL` (71–100).
- Supports both legacy action types (`READ_FILE`, `WRITE_FILE`) and Antigravity normalizer format (`FILE_READ`, `FILE_WRITE`, `COMMAND_EXECUTION`, `EXTERNAL_TRANSACTION`, etc.).

### 4. Automatic Security Intervention & Agent Pause
- When **Critical Drift** (≥ 75), **Critical Cumulative Risk** (≥ 70), consecutive high-risk actions, or constraint violations occur, the Security Gateway triggers **`PAUSE_AGENT`** and denies subsequent protected actions.
- The dashboard displays an emergency intervention banner with:
  - Intervention Reason & Divergent Action
  - Original Goal vs. Current Behavior
  - Interactive Controls: `[RESUME]`, `[STOP AGENT]`, `[MODIFY GOAL (V2)]`

### 5. Goal Versioning & In-Place Evolution
- Users can modify an active or paused goal in-place (e.g., intentionally authorizing backend additions).
- The system generates a new **`goalVersion`** (Version 1 → Version 2) with updated policy boundaries, preserving past actions in an immutable version history audit trail.

### 6. Explainable Security Decision Breakdown (`ActionDetailModal.jsx`)
- Every decision provides a 6-part pipeline breakdown:
  1. **Goal Alignment Score** (0–100% & Status)
  2. **Constraint Check** (PASSED / VIOLATED)
  3. **Scope Boundary Check** (ALLOWED / OUTSIDE SCOPE)
  4. **Contextual Risk** (Score & Level)
  5. **Multi-Step Goal Drift** (Score & Level)
  6. **Final Gateway Verdict** (`ALLOW`, `REQUIRE_APPROVAL`, `BLOCK`)
- Includes an explainable **"WHY?"** statement referencing the goal, action, constraint, and scope.

### 7. Action Classification
- Actions are categorized into:
  - `PRODUCTIVE` — Highly aligned, low risk, core feature delivery
  - `RELEVANT` — Safe investigative reads or test executions
  - `UNCERTAIN` — Boundary actions requiring human review
  - `UNRELATED` — Out-of-scope actions
  - `DANGEROUS` — Destructive operations, credential access, or constraint violations

### 8. Antigravity Connection Status
- The dashboard displays real-time connection status: `● CONNECTED` or `○ WAITING FOR ANTIGRAVITY`.
- Shows last event time, intercepted action count, active session ID, and goal binding.
- Connection status is based on **actual received events**, not merely whether the backend server is running.

### 9. Goal Integrity Trend Chart (Recharts)
- Real-time interactive visualization of:
  - **Rolling Goal Integrity** (cyan curve)
  - **Action Alignment** (emerald/amber/red points)
  - **Cumulative Risk** (pink curve)
  - **50% Warning Drift Threshold** reference line

---

## 🚀 Demonstration Scenarios

| Scenario | Objective | Agent Behavior | Expected Security Outcome |
|---|---|---|---|
| **Scenario A: Normal Agent** | *"Create React portfolio website with dark theme."* | Creates components (`Navbar.jsx`, `Hero.jsx`), updates CSS, runs tests. | **HIGH INTEGRITY (95%+)**, all `ALLOWED`, completes cleanly. |
| **Scenario B: Goal Drift** | *"Create React portfolio website."* | Creates components, then drifts into modifying `server.js` and `database.sql`. | Progressive drift → `BLOCKED` → **`⏸ AGENT PAUSED`** → User can **Modify Goal to V2** and resume. |
| **Scenario C: Security Violation** | *"Create React portfolio website."* | Attempts to access `.env`, delete database schema, and upload files externally. | **CRITICAL RISK (95%+)**, all `BLOCKED`, triggers immediate Security Pause. |

---

## 🏗️ Architecture Flow

### Google Antigravity → Agent Guard (Primary)

```
User Natural Language Goal
       ↓
Dynamic Goal Policy Generator (Objective, Allowed/Restricted Scope, Constraints)
       ↓
Human Confirmation (System Understanding)
       ↓
Google Antigravity (Autonomous Agent)
       ↓
Antigravity proposes tool action
       ↓
PreToolUse Hook (.agents/hooks.json)
       ↓
agent_guard_hook.py (stdin payload → HTTP)
       ↓
┌────────────────────────────────────────────────────────┐
│              AGENT GUARD SECURITY GATEWAY               │
│  1. Action Normalization (Antigravity → Generic)        │
│  2. Active Goal & Session Resolution                    │
│  3. Dynamic Goal Integrity Evaluation (0-100)           │
│  4. Multi-Step Goal Drift Detection (0-100)             │
│  5. Contextual & Cumulative Risk Engine (0-100)         │
│  6. Decision Matrix (ALLOW / REQUIRE_APPROVAL / BLOCK)  │
│  7. Automatic Security Pause Trigger Check              │
└───────────────────────────┬────────────────────────────┘
                            ↓
   ┌────────────────────────┼────────────────────────┐
   ↓                        ↓                        ↓
 ALLOW                    ASK                      DENY
   ↓                        ↓                        ↓
Antigravity            Antigravity             Tool BLOCKED
Executes Tool          Prompts User            (NOT EXECUTED)
   ↓                        ↓                        ↓
   └────────────────────────┴────────────────────────┘
                            ↓
              MongoDB Persistence & Audit Log
                            ↓
        Live AI Security Operations Center Dashboard
```

### Interception Boundary

Agent Guard intercepts supported Antigravity tool calls through the PreToolUse integration boundary. Supported tools include:
- **File operations**: `write_to_file`, `replace_file_content`, `multi_replace_file_content`, `view_file`, `list_dir`, `grep_search`
- **Commands**: `run_command`
- **Browser**: `browser_subagent`, `read_url_content`, `search_web`
- **Other**: `generate_image`, `ask_question`, and any MCP tool calls

### ASK Flow Limitation

The PreToolUse hook is synchronous — it returns a decision immediately. When the hook returns `"ask"`, Antigravity's own UI prompts the user for confirmation. The Agent Guard dashboard records the event as `PENDING_APPROVAL` for audit, but the actual approval happens in Antigravity's prompt. Full Agent Guard dashboard-driven approval requires the OpenAI agent loop mode.

---

## 💻 Tech Stack

- **Frontend**: React 19, Vite, Recharts, Lucide React, Vanilla CSS with custom glassmorphism design system.
- **Backend**: Python 3.13, FastAPI, Uvicorn, Motor (Async MongoDB), Pydantic v2.
- **Database**: MongoDB (Atlas / Local).
- **Integration**: Google Antigravity PreToolUse hooks.
- **Goal Analysis**: OpenAI API (optional, deterministic fallback included).

---

## ⚡ Quick Start

### 1. Prerequisites
- **Node.js** 18+ & **npm**
- **Python** 3.10+
- **MongoDB** running locally or via MongoDB Atlas
- **Google Antigravity** IDE or CLI

### 2. Backend Setup

```bash
cd backend

# Create virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables (.env)
# MONGODB_URI=mongodb+srv://... or mongodb://localhost:27017
# OPENAI_API_KEY=your_key_here (optional, offline dynamic synthesizer included)

# Start FastAPI Backend Server
uvicorn app.main:app --port 8000
```

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start Vite Development Server
npm run dev
```

Open [http://localhost:5173](http://localhost:5173) in your browser.

### 4. Antigravity Integration

The integration is pre-configured in `.agents/hooks.json`. When Agent Guard's backend is running on port 8000, every Antigravity tool call will be intercepted automatically.

**Usage Flow:**
1. Open the Agent Guard dashboard at `http://localhost:5173`
2. Enter your goal and constraints
3. Click **"ACCEPT & MONITOR (ANTIGRAVITY)"**
4. Use Antigravity normally — every tool action is intercepted and evaluated
5. Monitor the dashboard for real-time security decisions

---

## 🧪 Testing & Verification

### Automated Backend Tests (Pytest)
Run all unit and integration security tests:

```bash
cd backend
pytest
```

### Frontend Linting & Build Validation
```bash
cd frontend
npm run lint    # oxlint
npm run build   # vite build production bundle
```

---

## 📡 API Reference

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/goals/analyze` | Synthesizes dynamic Goal Policy from natural language |
| `POST` | `/api/goals` | Creates a new goal with initial Version 1 policy |
| `GET` | `/api/goals/{goalId}` | Retrieves goal document and active policy |
| `POST` | `/api/goals/{goalId}/start` | Starts the OpenAI agent loop (optional) |
| `POST` | `/api/goals/{goalId}/stop` | Stops a running agent |
| `POST` | `/api/goals/{goalId}/resume` | Resumes an automatically paused agent |
| `POST` | `/api/goals/{goalId}/modify` | Modifies active goal and creates Version 2 policy |
| `GET` | `/api/goals/{goalId}/history` | Retrieves goal version history trail |
| `GET` | `/api/goals/{goalId}/actions` | Returns full chronologically ordered action log |
| `GET` | `/api/goals/{goalId}/dashboard` | Returns rolling integrity, drift, risk, and trend data |
| `POST` | `/api/actions/{actionId}/approve` | Approves a pending action |
| `POST` | `/api/actions/{actionId}/reject` | Rejects a pending action |
| `POST` | `/api/agent/intercept` | **Antigravity interception endpoint** — evaluates a tool call |
| `GET` | `/api/agent/status` | Returns Antigravity connection status |
| `POST` | `/api/agent/session/bind` | Binds an Antigravity conversation to a goal |
| `POST` | `/api/demo/scenario/{scenarioId}` | Launches Scenario A, B, or C deterministic demos |
| `POST` | `/api/goals/{goalId}/reset` | Cleans up goal data and resets demo state |

---

## 📄 License

MIT License. Designed and developed as a hackathon prototype for runtime AI agent security and action authorization.
