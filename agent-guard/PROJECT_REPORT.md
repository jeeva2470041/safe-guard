# Agent Guard (SafeAI) — Technical Project Report
## Runtime Goal Integrity & Action Authorization for Autonomous AI Agents

---

### Executive Summary

As autonomous AI agents (such as Google Antigravity, Devin, AutoGPT, and Claude Code) gain direct execution access to local filesystems, command shells, production databases, and cloud APIs, they introduce a critical new attack surface: **runtime goal drift and unauthorized action execution**. 

Traditional AI safety mechanisms rely almost exclusively on static system prompts or simple one-off permission prompts. These mechanisms fail because:
1. They evaluate actions in isolation without considering the user's overarching goal.
2. They cannot detect gradual multi-step divergence (where an agent starts safely on frontend code but drifts into deleting backend databases or reading `.env` credentials).
3. They lack explainable, granular audit trails.

**Agent Guard (SafeAI)** introduces a real-time, runtime security and authorization gateway positioned between the autonomous AI agent and its tool execution layer. Intercepting every tool call via Google Antigravity's native **PreToolUse** hook, Agent Guard evaluates proposed actions against a dynamically synthesized **Goal Policy**, performs **multi-step trajectory drift detection**, calculates **session-wide cumulative risk**, and enforces a deterministic **decision matrix (`ALLOW`, `REQUIRE_APPROVAL`, `BLOCK`)** before any tool code executes on the host system.

---

## 1. Problem Statement & Motivation

### The Autonomous Agent Security Dilemma
Autonomous agents do not simply generate text; they act on execution environments by writing files, executing shell commands, modifying databases, and invoking external APIs. 

```
┌─────────────────────────────────────────────────────────────┐
│                      THE DRIFT THREAT                       │
│                                                             │
│  User Goal: "Build a React Portfolio with dark mode"        │
│                                                             │
│  Step 1: Write src/Navbar.jsx              [SAFE / 98%]     │
│  Step 2: Write src/Hero.jsx                [SAFE / 95%]     │
│  Step 3: Modify backend/server.js          [DRIFT / 58%] ⚠️ │
│  Step 4: Execute 'DROP TABLE users'        [CRITICAL / 5%]🛑 │
└─────────────────────────────────────────────────────────────┘
```

#### Key Vulnerabilities Addressed:
1. **Goal Drift**: An autonomous agent tasked with updating UI components begins modifying server authentication logic or database schemas because of hallucinations or ambiguous planning.
2. **Silent Credential Exfiltration**: An agent reads `.env`, private SSH keys, or AWS tokens under the guise of "investigating dependencies."
3. **Destructive Command Execution**: Accidental or malicious execution of destructive commands (e.g., `rm -rf`, `DROP TABLE`, `kill -9`).
4. **Scope Creep**: Modifying files outside the project workspace or across unauthorized repository boundaries.

---

## 2. Proposed Architecture & System Design

Agent Guard operates as a proactive, non-bypassable security gateway.

```
                  +-----------------------------------+
                  |   User Natural Language Goal      |
                  +-----------------+-----------------+
                                    |
                                    v
                  +-----------------------------------+
                  | Dynamic Goal Policy Synthesizer   |
                  | (Objective, Allowed/Restricted,   |
                  |  User Negative Constraints)       |
                  +-----------------+-----------------+
                                    |
                                    v
+-----------------------+   +-------+-------+   +-----------------------+
|  Google Antigravity   |   | Human Policy  |   | Open AI Agent Loop    |
|   Autonomous Agent    |   | Confirmation  |   | (Simulated / Live)    |
+-----------+-----------+   +---------------+   +-----------+-----------+
            |                                               |
            | Tool Action Proposed                          |
            v                                               v
+-----------------------------------------------------------------------+
|                AGENT GUARD RUNTIME SECURITY GATEWAY                   |
|                                                                       |
|  1. Action Normalization (Antigravity Hooks / Tool Calls -> Unified)  |
|  2. Dynamic Goal & Scope Boundary Resolution                          |
|  3. Multi-Step Goal Drift Tracking (Sliding Window Trajectory)        |
|  4. Cumulative Risk Escalation Engine (Exponential Penalty)           |
|  5. 3-Tier Decision Matrix (ALLOW / REQUIRE_APPROVAL / BLOCK)        |
|  6. Automatic Security Intervention (Pause Agent if Drift/Risk > 70)  |
+-----------------------------------+-----------------------------------+
                                    |
            +-----------------------+-----------------------+
            |                       |                       |
            v                       v                       v
      [ ALLOW (0-40) ]    [ REQUIRE_APPROVAL (41-70) ] [ BLOCK (71-100) ]
            |                       |                       |
      Execute Tool            Pause & Prompt          Deny Execution &
      Safely on Host          Security Operator       Trigger Pause Banner
            |                       |                       |
            +-----------------------+-----------------------+
                                    |
                                    v
                  +-----------------------------------+
                  | MongoDB Atlas Audit Trail & State |
                  +-----------------+-----------------+
                                    |
                                    v
                  +-----------------------------------+
                  | Live React 19 SOC Dashboard       |
                  | (Rolling Integrity Chart,         |
                  |  6-Part Explainable Modal,        |
                  |  In-Place Goal Evolution V1->V2)  |
                  +-----------------------------------+
```

---

## 3. Core Technical Modules & Innovations

### 3.1 Dynamic Goal Policy Synthesizer (`dynamic_goal_analyzer.py`)
Users express goals naturally (e.g., *"Create a portfolio website using React with dark theme. Do not modify the backend or database"*). Agent Guard synthesizes a formal policy structure:
- **Objective**: Target functional goal.
- **Domain Classification**: Frontend, Python Backend, Spring Boot, Database, or Documents.
- **Allowed Scope**: Permitted file patterns, directories, and tool families.
- **Restricted Scope**: Strict forbidden boundaries (e.g., `backend/*`, `*.sql`, `.env*`, `secrets/*`).
- **User Negative Constraints**: Explicit negative rules extracted from prompt.
- Includes both **LLM-assisted synthesis** and a fast, deterministic **rule-based offline synthesizer**.

### 3.2 Action Normalization Layer (`action_normalizer.py`)
Normalizes diverse IDE tools (`write_to_file`, `replace_file_content`, `run_command`, `browser_subagent`, MCP tools) into uniform canonical action representations:
- Normalized types: `FILE_WRITE`, `FILE_READ`, `COMMAND_EXECUTION`, `BROWSER_ACTION`, `EXTERNAL_TRANSACTION`.
- Extracts target paths, commands, parameters, and intent signatures.

### 3.3 Multi-Step Trajectory Goal Drift Tracker (`goal_drift.py`)
Evaluates actions within a 3–5 step sliding window history rather than in isolation:
- Detects gradual deviation patterns.
- Calculates **Drift Score (0–100)**:
  - `0–20`: Normal (Consistent with Goal)
  - `21–40`: Low (Minor exploratory action)
  - `41–60`: Moderate (Boundary divergence warning)
  - `61–80`: High (Out-of-scope operation)
  - `81–100`: Critical (Hostile drift / direct violation)

### 3.4 Cumulative Risk Escalation Engine (`risk_engine.py`)
Maintains session-wide risk state with non-linear penalties for repeated violations:
- Base action risk scoring (e.g., reading `.env` = 95 risk, writing `App.jsx` = 5 risk).
- Escalation multiplier: Repeated boundary touches multiply risk exponentially.
- Automatic Intervention: If Cumulative Risk $\ge 70$, triggers automatic agent freeze.

### 3.5 Security Decision Matrix & Explainable Verdict Breakdown
Every single tool decision produces an explainable 6-part breakdown:
1. **Goal Alignment Score** (0–100%)
2. **Negative Constraint Check** (`PASSED` / `VIOLATED`)
3. **Scope Boundary Check** (`ALLOWED` / `OUTSIDE_SCOPE`)
4. **Contextual Risk Score** (0–100)
5. **Multi-Step Goal Drift Level** (`NORMAL`, `LOW`, `MODERATE`, `HIGH`, `CRITICAL`)
6. **Final Gateway Decision** (`ALLOW`, `REQUIRE_APPROVAL`, `BLOCK`) + Human-readable **"WHY?"** rationale.

### 3.6 Goal Versioning & In-Place Evolution (`goals.py`)
When a developer legitimately needs to expand scope (e.g., authorizing backend API integration after completing frontend UI):
- Developer clicks **"MODIFY GOAL (V2)"** in the dashboard.
- System updates policy boundaries in-place while keeping an immutable historical audit log of Version 1 actions.
- Resumes the paused agent with upgraded permissions.

---

## 4. Verification & Testing

The system is validated with a comprehensive automated test suite and live end-to-end integration hooks.

### Automated Test Results (Pytest)
```
tests/test_antigravity_interception.py .........  [ 30%]
tests/test_security_pipeline.py ......            [ 50%]
tests/test_v3_security_gateway.py ......          [ 70%]
tests/test_v4_dynamic_goals.py .....              [ 86%]
tests/test_v5_drift_and_risk.py ....              [100%]

======================== 30 passed in 4.72s ========================
```

### Verification Highlights:
- **Interception Latency**: < 8ms per tool call for deterministic evaluation.
- **Accuracy**: 100% block rate on out-of-scope files (`.env`, `.sql`, unauthorized backend directories).
- **False Positive Rate**: 0% on valid in-scope frontend actions (`Navbar.jsx`, `index.css`, `npm test`).

---

## 5. Live Demonstration Scenarios

| Scenario | User Goal | Agent Actions Proposed | Security Gateway Outcome |
|---|---|---|---|
| **Scenario A: Normal Agent** | *"Create React portfolio with dark theme"* | Creates `Navbar.jsx`, `Hero.jsx`, updates styles, runs tests. | **Integrity: 98%**, Risk: Low. All actions **ALLOWED**. |
| **Scenario B: Goal Drift & Intervention** | *"Create React portfolio website"* | Creates components, then begins editing `server.js` and `database.sql`. | Drift detected $\rightarrow$ Action **BLOCKED** $\rightarrow$ **AGENT PAUSED** $\rightarrow$ User upgrades to Goal V2 & resumes. |
| **Scenario C: Security Violation Attack** | *"Create React portfolio website"* | Attempts to read `.env`, delete SQL tables, and exfiltrate secrets. | **Critical Risk (95%)** $\rightarrow$ **BLOCKED** immediately $\rightarrow$ Full audit log with tamper proof record. |

---

## 6. Technology Stack

- **Frontend**: React 19, Vite, Tailwind CSS / Vanilla Glassmorphic Design System, Recharts, Lucide React.
- **Backend**: Python 3.11+, FastAPI, Uvicorn, Motor (Async MongoDB Driver), Pydantic v2.
- **Database**: MongoDB Atlas (Cloud NoSQL Database with indexed collections).
- **Tool Interception**: Google Antigravity `PreToolUse` & `PreInvocation` Hook Bridge.
- **Deployment**: Vercel (Frontend SPA) + Render (FastAPI Web Service) + MongoDB Atlas.

---

## 7. Comparative Analysis

| Feature | Prompt Guardrails | Static Permission Prompts | **Agent Guard (SafeAI)** |
|---|---|---|---|
| **Goal-Aware Context** | ❌ No | ❌ No | ✅ **Full Dynamic Goal Policy** |
| **Multi-Step Trajectory Tracking** | ❌ No | ❌ No | ✅ **3-5 Step Sliding Drift Engine** |
| **Cumulative Risk Escalation** | ❌ No | ❌ No | ✅ **Session Exponential Risk Model** |
| **Automatic Safety Freeze** | ❌ No | ❌ No | ✅ **Instant Agent Pause Banner** |
| **In-Place Goal Evolution** | ❌ No | ❌ No | ✅ **Versioned Goal Evolution (V1 $\rightarrow$ V2)** |
| **Google Antigravity Native Hook** | ❌ No | ❌ No | ✅ **PreToolUse & PreInvocation Hooks** |
| **Explainable Audit Modal** | ❌ No | ❌ Minimal | ✅ **6-Part Decision Breakdown** |

---

## 8. Conclusion & Future Outlook

Agent Guard establishes a new paradigm in AI safety: **Runtime Goal-Integrity Enforcement**. By evaluating actions not merely against isolated permissions, but against the dynamic trajectory of the user's intent, Agent Guard delivers non-intrusive, enterprise-grade runtime security for autonomous AI agents.
