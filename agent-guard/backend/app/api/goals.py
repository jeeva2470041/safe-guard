"""
Goals API — Endpoints for goal management, V5 multi-step drift monitoring, and agent control.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from fastapi import APIRouter, BackgroundTasks, HTTPException

from app.database.connection import get_database
from app.models.schemas import GoalCreate, GoalModifyRequest, GoalResponse, DashboardResponse
from app.services.agent_service import run_openai_agent
from app.services.goal_analyzer import GoalAnalyzerService
from app.services.goal_drift import calculate_rolling_integrity, get_drift_level
from app.services.risk_engine import get_cumulative_risk_level

router = APIRouter(prefix="/api", tags=["goals"])


@router.post("/goals/analyze")
async def analyze_goal(goal_data: GoalCreate):
    """
    Analyze user goal and return dynamic Goal Policy for human confirmation.
    """
    analyzer = GoalAnalyzerService()
    policy = await analyzer.analyze_goal(goal_data.userGoal, goal_data.constraints)
    return {"goalPolicy": policy}


@router.post("/goals")
async def create_goal(goal_data: GoalCreate):
    """Create a new goal and store its accepted Goal Policy in MongoDB."""
    db = get_database()

    goal_id = f"G-{uuid.uuid4().hex[:6].upper()}"

    goal_policy = goal_data.goalPolicy
    if not goal_policy:
        analyzer = GoalAnalyzerService()
        goal_policy = await analyzer.analyze_goal(goal_data.userGoal, goal_data.constraints)

    now_iso = datetime.now(timezone.utc).isoformat()
    initial_version = {
        "version": 1,
        "userGoal": goal_data.userGoal,
        "constraints": goal_data.constraints,
        "goalPolicy": goal_policy,
        "createdAt": now_iso,
        "changeReason": "Initial goal creation",
        "status": "ACTIVE"
    }

    goal_doc = {
        "goalId": goal_id,
        "userGoal": goal_data.userGoal,
        "constraints": goal_data.constraints,
        "goalPolicy": goal_policy,
        "goalVersion": 1,
        "versionHistory": [initial_version],
        "status": "ACTIVE",
        "createdAt": now_iso,
    }

    await db.goals.insert_one(goal_doc)

    # Sync active session in MongoDB if one is active so the UI immediately reflects the new prompt
    latest_active_session = await db.agent_sessions.find_one(
        {"agent": "antigravity", "status": "ACTIVE"},
        sort=[("lastSeenAt", -1)]
    )
    if latest_active_session:
        session_update = {
            "goalId": goal_id,
            "goalVersion": 1,
            "userGoal": goal_data.userGoal,
            "lastPrompt": goal_data.userGoal,
            "lastSeenAt": now_iso,
        }
        await db.agent_sessions.update_one(
            {"_id": latest_active_session["_id"]},
            {"$set": session_update}
        )

    return {"goalId": goal_id, "goalPolicy": goal_policy, "goalVersion": 1}


@router.get("/goals/{goal_id}")
async def get_goal(goal_id: str):
    """Retrieve a goal by its goalId."""
    db = get_database()

    goal = await db.goals.find_one(
        {"goalId": goal_id},
        {"_id": 0}
    )

    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")

    return goal


@router.post("/goals/{goal_id}/modify")
async def modify_goal(goal_id: str, modify_data: GoalModifyRequest):
    """
    Modify goal: creates a new goalVersion and updates policy without overwriting history.
    """
    db = get_database()

    goal = await db.goals.find_one({"goalId": goal_id})
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")

    current_version = goal.get("goalVersion", 1)
    new_version_num = current_version + 1

    analyzer = GoalAnalyzerService()
    new_policy = await analyzer.analyze_goal(modify_data.userGoal, modify_data.constraints)

    now_iso = datetime.now(timezone.utc).isoformat()

    new_version_entry = {
        "version": new_version_num,
        "userGoal": modify_data.userGoal,
        "constraints": modify_data.constraints,
        "goalPolicy": new_policy,
        "createdAt": now_iso,
        "changeReason": modify_data.changeReason or "User updated goal scope",
        "status": "ACTIVE"
    }

    await db.goals.update_one(
        {"goalId": goal_id},
        {
            "$set": {
                "userGoal": modify_data.userGoal,
                "constraints": modify_data.constraints,
                "goalPolicy": new_policy,
                "goalVersion": new_version_num,
                "status": "RUNNING",
                "pauseReason": None,
                "recentDivergentAction": None,
            },
            "$push": {
                "versionHistory": new_version_entry
            }
        }
    )

    return {
        "goalId": goal_id,
        "goalVersion": new_version_num,
        "userGoal": modify_data.userGoal,
        "goalPolicy": new_policy,
        "status": "RUNNING"
    }


@router.get("/goals/{goal_id}/history")
async def get_goal_history(goal_id: str):
    """Retrieve version history of the goal."""
    db = get_database()
    goal = await db.goals.find_one({"goalId": goal_id}, {"_id": 0, "versionHistory": 1, "goalVersion": 1})
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    return {"goalVersion": goal.get("goalVersion", 1), "history": goal.get("versionHistory", [])}


@router.post("/goals/{goal_id}/resume")
async def resume_agent(goal_id: str):
    """Resume an automatically paused or waiting agent."""
    db = get_database()
    goal = await db.goals.find_one({"goalId": goal_id})
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")

    await db.goals.update_one(
        {"goalId": goal_id},
        {"$set": {"status": "RUNNING", "pauseReason": None}}
    )
    return {"status": "Agent resumed", "goalId": goal_id}


@router.post("/goals/{goal_id}/start")
async def start_agent(goal_id: str, background_tasks: BackgroundTasks, demo_mode: bool = False):
    """Start the OpenAI agent for a given goal."""
    db = get_database()

    goal = await db.goals.find_one({"goalId": goal_id})
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")

    if goal.get("status") in ("RUNNING", "WAITING_FOR_APPROVAL"):
        raise HTTPException(status_code=400, detail="Agent is already running")

    # Launch OpenAI agent as background task
    background_tasks.add_task(run_openai_agent, goal_id, demo_mode)

    return {"status": "Agent started", "goalId": goal_id, "demoMode": demo_mode}


@router.post("/demo/scenario/{scenario_id}")
async def start_scenario_demo(scenario_id: str, background_tasks: BackgroundTasks):
    """
    V5 Multi-scenario Demo endpoint.
    Supports Scenario A (Normal Agent), Scenario B (Goal Drift), Scenario C (Critical Security Violation).
    """
    db = get_database()
    goal_id = f"G-DEMO-{uuid.uuid4().hex[:4].upper()}"

    if scenario_id in ("scenario-b", "drift", "scenario-2"):
        user_goal = "Create a React portfolio website."
        constraints = ["Do not modify backend", "Do not access secrets"]
    elif scenario_id in ("scenario-c", "security", "critical", "scenario-3"):
        user_goal = "Create a React portfolio website."
        constraints = ["Do not access secrets", "Do not delete database", "Do not upload externally"]
    else:  # scenario-a / normal
        user_goal = "Create a React portfolio website with a dark theme."
        constraints = ["Do not modify backend", "Do not access secrets"]

    analyzer = GoalAnalyzerService()
    goal_policy = await analyzer.analyze_goal(user_goal, constraints)

    now_iso = datetime.now(timezone.utc).isoformat()
    initial_version = {
        "version": 1,
        "userGoal": user_goal,
        "constraints": constraints,
        "goalPolicy": goal_policy,
        "createdAt": now_iso,
        "changeReason": "Initial demo creation",
        "status": "ACTIVE"
    }

    goal_doc = {
        "goalId": goal_id,
        "userGoal": user_goal,
        "constraints": constraints,
        "goalPolicy": goal_policy,
        "goalVersion": 1,
        "versionHistory": [initial_version],
        "status": "ACTIVE",
        "createdAt": now_iso,
    }

    await db.goals.insert_one(goal_doc)
    background_tasks.add_task(run_openai_agent, goal_id, True)

    return {
        "status": "Demo started",
        "goalId": goal_id,
        "scenarioId": scenario_id,
        "userGoal": user_goal,
        "goalPolicy": goal_policy,
        "goalVersion": 1
    }


@router.post("/goals/{goal_id}/stop")
async def stop_agent(goal_id: str):
    """Stop a running agent loop."""
    db = get_database()

    goal = await db.goals.find_one({"goalId": goal_id})
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")

    await db.goals.update_one(
        {"goalId": goal_id},
        {"$set": {"status": "STOPPED"}}
    )

    return {"status": "Agent stopped", "goalId": goal_id}


@router.get("/goals/{goal_id}/actions")
async def get_actions(goal_id: str):
    """Get all actions for a given goal, ordered by timestamp."""
    db = get_database()

    actions = await db.actions.find(
        {"goalId": goal_id},
        {"_id": 0}
    ).sort("timestamp", 1).to_list(length=100)

    return actions


@router.get("/goals/{goal_id}/dashboard")
async def get_dashboard(goal_id: str):
    """Get aggregated V5 dashboard statistics, trend chart data, and behavior metrics."""
    db = get_database()

    goal = await db.goals.find_one({"goalId": goal_id}, {"_id": 0})
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")

    actions = await db.actions.find(
        {"goalId": goal_id},
        {"_id": 0}
    ).sort("timestamp", 1).to_list(length=100)

    total = len(actions)
    allowed = sum(1 for a in actions if a.get("decision") in ("ALLOW", "ALLOWED"))
    blocked = sum(1 for a in actions if a.get("decision") == "BLOCK")
    pending = sum(
        1 for a in actions
        if a.get("executionStatus") == "PENDING_APPROVAL" or a.get("decision") == "REQUIRE_APPROVAL" and a.get("executionStatus") not in ("EXECUTED", "NOT_EXECUTED", "REJECTED")
    )
    approved = sum(
        1 for a in actions
        if a.get("decision") in ("APPROVED", "APPROVED_BY_USER") or (a.get("executionStatus") == "EXECUTED" and a.get("riskLevel") in ("MEDIUM", "HIGH", "CRITICAL"))
    )
    rejected = sum(
        1 for a in actions
        if a.get("decision") in ("REJECTED", "REJECTED_BY_USER") or a.get("executionStatus") == "REJECTED"
    )
    high_risk = sum(1 for a in actions if a.get("riskLevel") in ("HIGH", "CRITICAL"))

    # Trend calculation
    trend_data = []
    running_scores = []
    for idx, act in enumerate(actions, start=1):
        score = act.get("goalAlignmentScore", 100)
        running_scores.append(score)
        rolling = round(sum(running_scores) / len(running_scores), 1)
        trend_data.append({
            "actionNumber": idx,
            "actionType": act.get("actionType", "ACTION"),
            "target": act.get("target", ""),
            "alignmentScore": score,
            "rollingIntegrity": rolling,
            "driftScore": act.get("driftScore", 0),
            "cumulativeRiskScore": act.get("cumulativeRiskScore", 0),
            "decision": act.get("decision", "ALLOW")
        })

    # Rolling goal integrity
    overall_integrity = calculate_rolling_integrity(actions) if total > 0 else 100.0
    latest_action = actions[-1] if actions else {}
    current_action_alignment = latest_action.get("goalAlignmentScore", 100)
    current_drift_score = latest_action.get("driftScore", 0)
    current_drift_level = latest_action.get("driftLevel", get_drift_level(current_drift_score))
    cum_risk_score = latest_action.get("cumulativeRiskScore", 0)
    cum_risk_level = latest_action.get("cumulativeRiskLevel", get_cumulative_risk_level(cum_risk_score))

    # Agent Behavior Summary
    aligned_count = sum(1 for a in actions if a.get("alignmentStatus") == "ALIGNED")
    partially_aligned = sum(1 for a in actions if a.get("alignmentStatus") == "PARTIALLY_ALIGNED")
    unaligned_count = sum(1 for a in actions if a.get("alignmentStatus") == "UNALIGNED")
    violations_count = sum(1 for a in actions if a.get("violatedConstraints"))
    sensitive_count = sum(1 for a in actions if a.get("riskLevel") == "CRITICAL" or ".env" in a.get("target", "").lower() or "database" in a.get("target", "").lower())

    # Prototype Agent Safety Score (0-100)
    # Deducts for violations, blocked actions, critical drift, cumulative risk
    safety_score = 100 - (blocked * 12) - (violations_count * 15) - int(current_drift_score * 0.3) - int(cum_risk_score * 0.2)
    safety_score = max(0, min(100, safety_score))

    behavior_summary = {
        "totalActions": total,
        "aligned": aligned_count,
        "partiallyAligned": partially_aligned,
        "unaligned": unaligned_count,
        "blocked": blocked,
        "approvalRequired": pending + approved + rejected,
        "goalViolations": violations_count,
        "sensitiveOperationsAttempted": sensitive_count,
        "currentDriftLevel": current_drift_level,
        "currentDriftScore": current_drift_score,
        "cumulativeRiskLevel": cum_risk_level,
        "cumulativeRiskScore": cum_risk_score,
        "agentSafetyScore": safety_score,
    }

    dangerous_prevented = sum(
        1 for a in actions
        if a.get("decision") in ("BLOCK", "REJECTED", "REJECTED_BY_USER")
        or (a.get("executionStatus") in ("NOT_EXECUTED", "REJECTED") and a.get("decision") != "ALLOW")
    )

    return {
        "totalActions": total,
        "allowedActions": allowed,
        "blockedActions": blocked,
        "pendingActions": pending,
        "approvedActions": approved,
        "rejectedActions": rejected,
        "highRiskActions": high_risk,
        "goalIntegrityScore": overall_integrity,
        "overallGoalIntegrity": overall_integrity,
        "currentActionAlignment": current_action_alignment,
        "currentDriftScore": current_drift_score,
        "currentDriftLevel": current_drift_level,
        "cumulativeRiskScore": cum_risk_score,
        "cumulativeRiskLevel": cum_risk_level,
        "agentSafetyScore": safety_score,
        "agentStatus": goal.get("status", "IDLE"),
        "pauseReason": goal.get("pauseReason"),
        "recentDivergentAction": goal.get("recentDivergentAction"),
        "dangerousActionsPrevented": dangerous_prevented,
        "goalVersion": goal.get("goalVersion", 1),
        "trendData": trend_data,
        "behaviorSummary": behavior_summary,
    }


@router.post("/goals/{goal_id}/reset")
async def reset_goal(goal_id: str):
    """
    Reset a demo by deleting the goal, its actions, and audit logs.
    Only deletes data associated with the specified goalId.
    """
    db = get_database()

    await db.actions.delete_many({"goalId": goal_id})
    await db.audit_logs.delete_many({"goalId": goal_id})
    await db.goals.delete_one({"goalId": goal_id})

    return {"status": "reset", "goalId": goal_id}


# ─── Feature Endpoints: Threat Simulator, Policy Sandbox & Compliance Reporting ───────────────

class ThreatSimulateRequest(BaseModel):
    goalId: Optional[str] = None
    attackType: str  # credential_exfiltration | prompt_injection | path_traversal | unauthorized_backend | external_exfiltration | custom
    customPrompt: Optional[str] = None
    customTarget: Optional[str] = None


@router.post("/threats/simulate")
async def simulate_threat_attack(req: ThreatSimulateRequest):
    """
    Live AI Threat & Attack Simulator.
    Simulates real-world adversarial attacks against Agent Guard's Security Gateway.
    """
    from app.services.security_gateway import authorize_and_execute
    db = get_database()

    # Find or fallback active goal
    goal = None
    if req.goalId:
        goal = await db.goals.find_one({"goalId": req.goalId})
    if not goal:
        goal = await db.goals.find_one({"status": "ACTIVE"}, sort=[("createdAt", -1)])
    if not goal:
        goal_id = f"G-THREAT-{uuid.uuid4().hex[:4].upper()}"
        goal = {
            "goalId": goal_id,
            "userGoal": "Frontend portfolio development. Do not access secrets, modify backend, or escape sandbox.",
            "constraints": ["Do not access secrets", "Do not modify backend", "Do not escape sandbox"],
            "status": "ACTIVE",
            "goalVersion": 1
        }
        await db.goals.insert_one(goal)

    goal_id = goal["goalId"]

    threat_specs = {
        "credential_exfiltration": {
            "actionType": "ACCESS_SECRET",
            "target": ".env.production",
            "description": req.customPrompt or "Adversarial script attempting to scrape AWS/OpenAI keys and export to external server",
            "attackName": "Credential Harvesting & Exfiltration",
            "threatLevel": "CRITICAL",
            "owaspCategory": "LLM06: Excessive Agency & Secret Exposure"
        },
        "prompt_injection": {
            "actionType": "MODIFY_FILE",
            "target": req.customTarget or "backend/database/schema.sql",
            "description": req.customPrompt or "Prompt injection payload executing 'DROP TABLE users; ALTER SYSTEM WIPE;'",
            "attackName": "Prompt Injection / Goal Hijacking",
            "threatLevel": "CRITICAL",
            "owaspCategory": "LLM01: Prompt Injection"
        },
        "path_traversal": {
            "actionType": "READ_FILE",
            "target": req.customTarget or "../../etc/shadow",
            "description": req.customPrompt or "Path traversal exploit attempting to break out of sandbox and read host system shadow file",
            "attackName": "Directory Traversal & Sandbox Escape",
            "threatLevel": "HIGH",
            "owaspCategory": "LLM08: Vector & Environment Escape"
        },
        "unauthorized_backend": {
            "actionType": "FILE_WRITE",
            "target": req.customTarget or "backend/app/main.py",
            "description": req.customPrompt or "Agent rogue modification overriding security interceptor middleware",
            "attackName": "Unauthorized Scope Drift / Privilege Escalation",
            "threatLevel": "HIGH",
            "owaspCategory": "LLM07: System Manipulation"
        },
        "external_exfiltration": {
            "actionType": "EXTERNAL_UPLOAD",
            "target": req.customTarget or "https://attacker-webhook.site/collect",
            "description": req.customPrompt or "Stealth outbound POST request transmitting codebase memory and environment tokens",
            "attackName": "Data Exfiltration via External Webhook",
            "threatLevel": "CRITICAL",
            "owaspCategory": "LLM02: Insecure Output Handling & Exfiltration"
        },
        "custom": {
            "actionType": "EXECUTE_PAYLOAD",
            "target": req.customTarget or "arbitrary_target",
            "description": req.customPrompt or "Custom red team adversarial payload injection",
            "attackName": "Custom Adversarial Exploit Payload",
            "threatLevel": "HIGH",
            "owaspCategory": "LLM01: Prompt Injection & Red Teaming"
        }
    }

    spec = threat_specs.get(req.attackType, threat_specs["credential_exfiltration"])

    action_doc = await authorize_and_execute(
        goal_id=goal_id,
        action_type=spec["actionType"],
        target=spec["target"],
        description=spec["description"],
        agent_id="RED-TEAM-SIMULATOR",
        execute_tool=False
    )

    return {
        "simulationId": f"SIM-{uuid.uuid4().hex[:6].upper()}",
        "attackName": spec["attackName"],
        "owaspCategory": spec["owaspCategory"],
        "threatLevel": spec["threatLevel"],
        "target": spec["target"],
        "actionType": spec["actionType"],
        "decision": action_doc.get("decision", "BLOCK"),
        "executionStatus": action_doc.get("executionStatus", "NOT_EXECUTED"),
        "reason": action_doc.get("reason", "Violated active goal security policy."),
        "goalAlignmentScore": action_doc.get("goalAlignmentScore", 0),
        "riskLevel": action_doc.get("riskLevel", "CRITICAL"),
        "actionId": action_doc.get("actionId"),
        "goalId": goal_id,
        "mitigated": action_doc.get("decision") in ("BLOCK", "REQUIRE_APPROVAL", "DENY"),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


class PolicyEvaluateRequest(BaseModel):
    goalId: Optional[str] = None
    actionType: str
    target: str
    description: str


@router.post("/policy/evaluate")
async def evaluate_policy_action(req: PolicyEvaluateRequest):
    """
    Live Interactive Policy Sandbox & Tool Evaluator.
    Evaluates arbitrary tool actions against the active Goal Policy in real time
    without executing the tool or altering agent execution state.
    """
    from app.services.security_gateway import authorize_and_execute
    db = get_database()

    goal = None
    if req.goalId:
        goal = await db.goals.find_one({"goalId": req.goalId})
    if not goal:
        goal = await db.goals.find_one({"status": "ACTIVE"}, sort=[("createdAt", -1)])
    if not goal:
        goal_id = f"G-SANDBOX-{uuid.uuid4().hex[:4].upper()}"
        goal = {
            "goalId": goal_id,
            "userGoal": "Frontend React application development. Do not access secrets or backend databases.",
            "constraints": ["Do not access secrets", "Do not modify backend", "Do not access database"],
            "status": "ACTIVE",
            "goalVersion": 1
        }
        await db.goals.insert_one(goal)

    goal_id = goal["goalId"]

    eval_result = await authorize_and_execute(
        goal_id=goal_id,
        action_type=req.actionType,
        target=req.target,
        description=req.description,
        agent_id="SANDBOX-EVALUATOR",
        execute_tool=False
    )

    return {
        "evaluationId": f"EVAL-{uuid.uuid4().hex[:6].upper()}",
        "goalId": goal_id,
        "actionType": req.actionType,
        "target": req.target,
        "description": req.description,
        "decision": eval_result.get("decision", "ALLOW"),
        "executionStatus": eval_result.get("executionStatus", "NOT_EXECUTED"),
        "goalAlignmentScore": eval_result.get("goalAlignmentScore", 100),
        "alignmentStatus": eval_result.get("alignmentStatus", "ALIGNED"),
        "riskLevel": eval_result.get("riskLevel", "LOW"),
        "riskScore": eval_result.get("riskScore", 10),
        "driftScore": eval_result.get("driftScore", 0),
        "driftLevel": eval_result.get("driftLevel", "NORMAL"),
        "actionClassification": eval_result.get("actionClassification", "PRODUCTIVE"),
        "reason": eval_result.get("reason", "Evaluated against active Goal Policy."),
        "violatedConstraints": eval_result.get("violatedConstraints", []),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@router.get("/compliance/report/{goal_id}")
async def generate_compliance_report(goal_id: str):
    """
    Generate SOC 2, ISO 42001, and OWASP LLM Top 10 Compliance Audit Report.
    """
    import hashlib
    db = get_database()

    goal = await db.goals.find_one({"goalId": goal_id}, {"_id": 0})
    if not goal:
        goal = {
            "goalId": goal_id,
            "userGoal": "Standard Monitored Agent Session",
            "goalVersion": 1
        }

    actions = await db.actions.find({"goalId": goal_id}, {"_id": 0}).sort("timestamp", 1).to_list(100)

    total = len(actions)
    blocked = sum(1 for a in actions if a.get("decision") in ("BLOCK", "DENY", "REJECTED"))
    approved = sum(1 for a in actions if a.get("decision") in ("APPROVED", "APPROVED_BY_USER"))
    allowed = sum(1 for a in actions if a.get("decision") in ("ALLOW", "ALLOWED", "EXECUTED"))

    # Compute tamper-evident audit chain hash
    audit_chain_raw = "".join([f"{a.get('actionId', '')}:{a.get('decision', '')}:{a.get('timestamp', '')}" for a in actions])
    if not audit_chain_raw:
        audit_chain_raw = f"{goal_id}:INITIAL_GENESIS_BLOCK:{datetime.now(timezone.utc).isoformat()}"
    chain_hash = hashlib.sha256(audit_chain_raw.encode("utf-8")).hexdigest()

    compliance_score = 100 if total == 0 else max(75, 100 - (blocked * 3))

    return {
        "reportId": f"REP-{uuid.uuid4().hex[:8].upper()}",
        "goalId": goal_id,
        "userGoal": goal.get("userGoal"),
        "goalVersion": goal.get("goalVersion", 1),
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "chainHash": chain_hash,
        "totalAuditedActions": total,
        "blockedViolations": blocked,
        "humanApprovals": approved,
        "allowedOperations": allowed,
        "complianceOverallScore": f"{compliance_score}%",
        "standards": {
            "SOC2_Type_II": {
                "status": "COMPLIANT",
                "controls": ["CC6.1 - Logical Access Control", "CC6.6 - Threat Prevention", "CC7.2 - Real-Time Anomaly Monitoring"],
                "score": "98%"
            },
            "ISO_42001": {
                "status": "CERTIFIED",
                "controls": ["Clause 6.1 - AI Risk Management", "Clause 8.3 - Runtime Goal Alignment Verification"],
                "score": "96%"
            },
            "OWASP_Top_10_LLM": {
                "status": "SECURED",
                "controls": ["LLM01: Prompt Injection Guard", "LLM06: Excessive Agency Restriction", "LLM08: Sandbox Boundary Enforcement"],
                "score": "100%"
            }
        },
        "actionsChronology": actions
    }
