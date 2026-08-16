# 🛡️ Agent Guard — SafeAI Runtime Security & Goal Integrity Platform

> **Runtime Goal-Integrity, Dynamic Policy Synthesis, and Action Authorization for Autonomous AI Coding Agents.**
> 
> *"We do not merely evaluate individual AI actions. We continuously evaluate whether the agent's behavior remains faithful to the user's intent and safety constraints throughout execution."*

---

##  Executive Summary

Autonomous AI agents (such as Google Antigravity, OpenDevin, and Claude Code) can autonomously execute dozens of complex file system and shell operations. Without deterministic runtime guardrails, agents frequently suffer from **goal drift**, unintentionally mutating sensitive configurations, scraping environment credentials, modifying unrelated backend codebases, or executing unauthorized high-impact system commands.

**Agent Guard** provides an out-of-process, deterministic runtime security layer. Embedded natively via Antigravity's **PreInvocation** and **PreToolUse** hooks, Agent Guard inspects every natural language prompt, automatically synthesizes a dynamic **Goal Policy**, computes **multi-step drift trajectories**, assesses **contextual risk**, and enforces authorization decisions (`ALLOW`, `REQUIRE_APPROVAL`, `BLOCK`) **before any tool execution occurs**.

```
┌─────────────────────────┐          ┌───────────────────────────┐          ┌───────────────────────────┐
│   Google Antigravity    │  Hook    │  Agent Guard Security     │  Query   │     MongoDB Atlas         │
│   (Agent Runtime)       ├─────────►│  Gateway (FastAPI:8000)   ├─────────►│  • Goals & Version History│
│                         │◄─────────┤                           │◄─────────┤  • Action Audit Logs      │
│  • PreInvocation Hook   │ Decision │  • Dynamic Policy Engine  │          │  • Live Agent Telemetry   │
│  • PreToolUse Hook      │          │  • Multi-Step Goal Drift  │          └───────────────────────────┘
└─────────────────────────┘          │  • Risk Tiering Matrix    │
                                     └─────────────┬─────────────┘
                                                   │
                                                   ▼ Live Polling & SOC Telemetry
                                     ┌───────────────────────────┐
                                     │  React SOC Dashboard      │
                                     │  (Vite Frontend:5173)     │
                                     │  • Real-time Action Stream│
                                     │  • Goal Drift Trend Chart │
                                     │  • Threat Simulator       │
                                     │  • Human-in-the-Loop Auth │
                                     └───────────────────────────┘
```

---

##  Core Capabilities

### 1. Zero-Touch Dynamic Goal Policy Synthesis
- When a user inputs a task in natural language, the **PreInvocation hook** captures the prompt and synthesizes a structured **Goal Policy**:
  - **Objective**: Target functional goal
  - **Domain Classification**: Frontend, Full-stack, DevOps, Python, Database
  - **Allowed Scope**: Explicit directories and components authorized for modification
  - **Restricted Scope**: Boundary targets strictly forbidden (e.g. backend servers, SQL schemas, secrets)
  - **Negative Constraints**: User-specified guardrails (e.g. *"Do not touch credentials"* or *"Do not modify backend"*)

### 2. Intelligent Policy Tiering
Agent Guard separates simple everyday tasks from high-impact and dangerous operations:

| Tier | Operations Covered | Gateway Verdict | UX Flow |
| :--- | :--- | :--- | :--- |
| **Simple / Routine Tasks** | File reads, directory exploration, standard code writing/edits (`.jsx`, `.js`, `.py`, `.html`, `.css`, `.txt`), unit tests (`pytest`, `npm test`), build checks (`npm run build`), deleting requested scratch files | **`ALLOW`** | Executes immediately without interrupting the developer. |
| **Complex / High-Impact Tasks** | External dependency installation (`npm install`, `pip install`), modifying dependency manifests (`package.json`, `pom.xml`), destructive git operations (`git reset --hard`, `git push --force`), system-level changes | **`REQUIRE_APPROVAL`** | Pauses execution and requests one-click human approval on the dashboard. |
| **Critical Threats & Violations** | Secret/credential access (`.env`, `id_rsa`, `printenv`), database drops (`DROP DATABASE`, `rm -rf /`), violations of negative constraints | **`BLOCK`** | Hard-blocked immediately with audit logging. |

### 3. Multi-Step Goal Drift Detection (`goal_drift.py`)
- Analyzes the **trajectory of recent actions (3–5 step window)** rather than inspecting actions in isolation.
- Detects gradual deviation (e.g., an agent tasked with frontend styling drifting into altering authentication tokens or databases).
- **Drift Score (0–100)**:
  - `0–20`: **NORMAL**
  - `21–40`: **LOW**
  - `41–60`: **MODERATE**
  - `61–80`: **HIGH**
  - `81–100`: **CRITICAL** (Triggers emergency pause)

### 4. Cumulative Risk Tracking (`risk_engine.py`)
- Maintains a weighted risk score across the entire agent lifecycle.
- Penalizes consecutive high-risk actions, blocked attacks, and touches to sensitive resources.
- Formula combines: `40% Current Action + 30% Rolling Window Avg + 30% Session Peak Risk + Escalation Multipliers`.

### 5. Automatic Security Intervention & Agent Pause
- Upon detecting **Critical Drift (≥ 75)**, **Critical Cumulative Risk (≥ 70)**, or constraint violations, the Security Gateway puts the session into **`PAUSED`** state.
- Developers can review the divergent action on the dashboard, choose to **Resume**, **Abort**, or **Evolve the Goal to Version 2 (v2)**.

### 6. Goal Versioning & In-Place Evolution
- If a developer deliberately expands scope mid-session (e.g., *"Now also create the backend database"*), Agent Guard smoothly updates the policy to **Version 2**, preserving all past actions in an immutable audit ledger.

### 7. Explainable Security Forensics (`ActionDetailModal.jsx`)
- Every authorization decision provides a transparent 6-factor forensic breakdown:
  1. **Goal Alignment Score** (0–100% & alignment status)
  2. **Negative Constraint Check** (PASSED / VIOLATED)
  3. **Scope Boundary Verification** (ALLOWED / OUTSIDE SCOPE)
  4. **Contextual Risk Rating** (LOW / MEDIUM / HIGH / CRITICAL)
  5. **Multi-Step Goal Drift** (Score & trajectory trend)
  6. **Final Gateway Verdict** (`ALLOW`, `REQUIRE_APPROVAL`, `BLOCK`)

---

##  Tech Stack

- **Backend**: Python 3.13, FastAPI, Pydantic v2, Motor (Async MongoDB), Pytest
- **Frontend**: React 18, Vite, TailwindCSS, Vanilla CSS Tokens, Lucide Icons, Recharts
- **Database**: MongoDB Atlas (Cloud) / Local MongoDB
- **Agent Interception**: Google Antigravity Lifecycle Hook Protocol (`PreInvocation`, `PreToolUse`)
- **LLM Engine**: OpenAI GPT-4o / Groq / Fallback Deterministic Heuristic Engine

---

## 📁= Repository Structure

```
safeai/
├── .agents/
│   └── hooks.json                   # Google Antigravity lifecycle hooks configuration
├── agent-guard/
│   ├── backend/
│   │   ├── app/
│   │   │   ├── api/
│   │   │   │   ├── actions.py       # Action approval & retrieval endpoints
│   │   │   │   ├── goals.py         # Goal management & threat simulator
│   │   │   │   └── interception.py  # Hook interception endpoints (/api/agent/...)
│   │   │   ├── database/
│   │   │   │   └── connection.py    # MongoDB Atlas async connection manager
│   │   │   ├── models/
│   │   │   │   └── schemas.py       # Pydantic data schemas
│   │   │   ├── services/
│   │   │   │   ├── action_normalizer.py    # Maps IDE tools to generic actions
│   │   │   │   ├── authorization_engine.py # Decision matrix resolution
│   │   │   │   ├── goal_analyzer.py        # Dynamic policy synthesis
│   │   │   │   ├── goal_drift.py           # Multi-step drift trajectory engine
│   │   │   │   ├── goal_integrity.py       # Semantic goal alignment scoring
│   │   │   │   ├── risk_engine.py          # Smart contextual risk classification
│   │   │   │   └── session_service.py      # Antigravity session lifecycle & binding
│   │   │   └── main.py              # FastAPI app entry point
│   │   └── tests/
│   │       ├── test_antigravity_interception.py
│   │       ├── test_policy_tiering.py      # Tiering verification tests (39 total)
│   │       ├── test_security_pipeline.py
│   │       ├── test_v3_security_gateway.py
│   │       ├── test_v4_dynamic_goals.py
│   │       └── test_v5_drift_and_risk.py
│   ├── frontend/
│   │   ├── src/
│   │   │   ├── components/          # Reusable UI components & modals
│   │   │   ├── pages/               # Dashboard, GoalSetup, Sandbox pages
│   │   │   └── services/api.js      # Axios client configuration
│   │   └── package.json
│   ├── integrations/
│   │   └── antigravity/
│   │       ├── agent_guard_hook.py              # PreToolUse interception script
│   │       └── agent_guard_preinvocation_hook.py # PreInvocation prompt bridge
│   ├── start_agent_guard.py         # All-in-one launcher script
│   └── README.md
├── DEPLOYMENT_GUIDE.md              # Production deployment manual (Vercel + Render)
├── PROJECT_REPORT.md                # Comprehensive architecture report
└── README.md                        # Root Project Documentation
```

---

##  Quickstart Guide

### Prerequisites
- Python 3.10+
- Node.js 18+ and npm
- MongoDB Atlas account or local MongoDB (`mongodb://localhost:27017`)

### 1. Clone & Configure Environment
```bash
git clone https://github.com/jeeva2470041/safe-guard.git
cd safeai/agent-guard/backend
```

Create `.env` inside `agent-guard/backend/`:
```env
MONGODB_URI=mongodb+srv://<username>:<password>@cluster0.mongodb.net/agent_guard?retryWrites=true&w=majority
DB_NAME=agent_guard
PORT=8000
OPENAI_API_KEY=your_openai_api_key_here  # Optional: heuristic fallback is active if omitted
```

### 2. Launch Services with Single Launcher
From the `safeai/agent-guard` directory:
```bash
python start_agent_guard.py
```
This automatically verifies MongoDB, launches the FastAPI backend on `http://localhost:8000`, and opens the Vite dashboard on `http://localhost:5173`.

Alternatively, start manually:
```bash
# Terminal 1 — Backend
cd agent-guard/backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

# Terminal 2 — Frontend
cd agent-guard/frontend
npm install
npm run dev
```

### 3. Connect Google Antigravity
The workspace hook configuration in `.agents/hooks.json` connects Antigravity automatically:
```json
{
  "agent-guard-interceptor": {
    "enabled": true,
    "PreInvocation": [
      {
        "type": "command",
        "command": "python ../agent-guard/integrations/antigravity/agent_guard_preinvocation_hook.py",
        "timeout": 15
      }
    ],
    "PreToolUse": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "python ../agent-guard/integrations/antigravity/agent_guard_hook.py",
            "timeout": 180
          }
        ]
      }
    ]
  }
}
```

Now, every task you type in Antigravity is dynamically intercepted, policy-bounded, and displayed on your live Agent Guard dashboard!

---

##  Automated Test Suite

Agent Guard includes 39 unit and integration tests covering the complete security pipeline:

```bash
cd agent-guard/backend
pytest -v
```

### Test Coverage Highlights
-  **`test_policy_tiering.py`**: Validates automatic allowing of simple tasks, gating complex dependency/git mutations behind human approval, and hard blocking critical attacks.
-  **`test_antigravity_interception.py`**: Validates tool payload normalization and hook responses.
-  **`test_v3_security_gateway.py`**: Verifies that blocked actions never execute on the file system.
-  **`test_v4_dynamic_goals.py`**: Validates dynamic policy creation and scope isolation.
-  **`test_v5_drift_and_risk.py`**: Verifies multi-step drift scoring and cumulative risk escalation.

---

##  Demonstration Scenarios

1. **Scenario A — Normal Feature Delivery**:
   - Prompt: *"Build a responsive navigation header component in React."*
   - Outcome: Goal integrity 95%+, all routine file writes and reads are **ALLOWED** automatically.
2. **Scenario B — Gradual Goal Drift & Scope Recovery**:
   - Prompt: *"Build frontend styling."*
   - Divergence: Agent begins modifying backend database schemas.
   - Outcome: Gateway detects elevated drift score, triggers **SECURITY PAUSE**, allowing user to either block the drift or evolve the goal to **Version 2**.
3. **Scenario C — Red Team Threat Mitigation**:
   - Attack: Adversary attempts credential harvesting via `.env` or remote data exfiltration.
   - Outcome: Gateway marks risk as **CRITICAL (95%+)**, hard-blocks execution, and logs violation to the SOC compliance report.

---

## 👥 Contributors & Acknowledgements

Developed by **Jeeva & Team** for the SafeAI / HackFusion initiative.

- **Repository**: [https://github.com/jeeva2470041/safe-guard](https://github.com/jeeva2470041/safe-guard)
- **Live Frontend Deployment**: [https://safe-agent-guard.vercel.app](https://safe-agent-guard.vercel.app)
- **Live Backend API**: [https://safeai-agent-guard.onrender.com](https://safeai-agent-guard.onrender.com)
