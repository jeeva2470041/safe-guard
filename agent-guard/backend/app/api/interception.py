"""
Interception API — Endpoint for intercepting and authorizing external agent (Google Antigravity) tool calls.
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.action_normalizer import normalize_antigravity_action
from app.services.session_service import (
    resolve_active_goal_for_session,
    get_antigravity_connection_status,
    bind_session,
    start_or_update_antigravity_session
)
from app.services.security_gateway import authorize_and_execute
from app.models.schemas import SessionStartRequest, SessionStartResponse
from app.database.connection import get_database

logger = logging.getLogger("agent_guard.interception")

router = APIRouter(prefix="/api/agent", tags=["agent-interception"])


class InterceptRequest(BaseModel):
    toolCall: Dict[str, Any] = Field(default_factory=dict)
    conversationId: Optional[str] = None
    sessionId: Optional[str] = None
    workspacePaths: Optional[list] = None
    stepIdx: Optional[int] = None
    agent: Optional[str] = "antigravity"


class SessionBindRequest(BaseModel):
    conversationId: str
    goalId: str
    agent: Optional[str] = "antigravity"


@router.post("/session/start", response_model=SessionStartResponse)
async def start_session(req: SessionStartRequest):
    """
    Called by PreInvocation hook when user inputs a prompt into Antigravity.
    Automatically generates dynamic Goal Policy and binds conversationId -> goalId -> goalVersion.
    """
    result = await start_or_update_antigravity_session(
        conversation_id=req.conversationId,
        user_prompt=req.userPrompt,
        workspace_paths=req.workspacePaths,
        invocation_num=req.invocationNum or 1,
        agent=req.agent or "antigravity"
    )
    return result


@router.get("/session/active")
async def get_active_session():
    """Get current active Antigravity session and goal for dashboard auto-sync."""
    status = await get_antigravity_connection_status()
    return status


@router.post("/intercept")
async def intercept_tool_action(req: InterceptRequest):
    """
    Intercept an Antigravity tool call BEFORE execution.
    Normalizes action, evaluates against active Goal Policy in Security Gateway,
    and returns authorization decision (allow | deny | ask).
    """
    db = get_database()

    tool_call = req.toolCall or {}
    if not tool_call or not tool_call.get("name"):
        return {
            "decision": "allow",
            "reason": "Empty or unrecognized tool call."
        }

    # 1. Resolve active goal
    goal = await resolve_active_goal_for_session(
        conversation_id=req.conversationId,
        session_id=req.sessionId
    )

    if not goal:
        # If no goal is active, create a fallback baseline goal for this session
        goal_id = f"G-AUTO-{req.conversationId[:6] if req.conversationId else 'DEFAULT'}"
        user_goal = "Autonomous coding and file modification session"
        goal = {
            "goalId": goal_id,
            "userGoal": user_goal,
            "constraints": ["Do not delete system files", "Do not access credentials"],
            "status": "ACTIVE",
            "goalVersion": 1
        }
        await db.goals.update_one({"goalId": goal_id}, {"$setOnInsert": goal}, upsert=True)

    goal_id = goal["goalId"]

    # 2. Normalize Antigravity Tool Call into Generic Action
    normalized = normalize_antigravity_action(tool_call, req.workspacePaths)

    # 3. Evaluate through Security Gateway (execute_tool=False, Antigravity executes if allowed)
    action_doc = await authorize_and_execute(
        goal_id=goal_id,
        action_type=normalized["actionType"],
        target=normalized["target"],
        description=normalized["description"],
        agent_id="GOOGLE-ANTIGRAVITY",
        execute_tool=False,
        source=normalized.get("source", "AGENT_PLAN"),
        purpose=normalized.get("purpose"),
        consequence=normalized.get("consequence"),
        consequence_level=normalized.get("consequenceLevel", "LOW"),
        reversibility=normalized.get("reversibility", "REVERSIBLE")
    )

    gateway_decision = action_doc.get("decision", "ALLOW")

    # 4. Map Gateway decision to Antigravity hook protocol: allow | deny | ask
    if gateway_decision in ("ALLOW", "APPROVED"):
        antigravity_decision = "allow"
    elif gateway_decision == "REQUIRE_APPROVAL":
        antigravity_decision = "ask"
    else:  # BLOCK
        antigravity_decision = "deny"

    # Redact sensitive parameters from logging
    logger.info(
        f"[INTERCEPT] Tool: {normalized['rawToolName']} -> Action: {normalized['actionType']} "
        f"Target: {normalized['target']} => Decision: {antigravity_decision.upper()}"
    )

    return {
        "decision": antigravity_decision,
        "actionId": action_doc.get("actionId"),
        "gatewayDecision": gateway_decision,
        "executionStatus": action_doc.get("executionStatus"),
        "goalId": goal_id,
        "goalVersion": action_doc.get("goalVersion", 1),
        "normalizedActionType": normalized["actionType"],
        "target": normalized["target"],
        "source": action_doc.get("source", "USER"),
        "purpose": action_doc.get("purpose"),
        "goalRelationship": action_doc.get("goalRelationship", "SUPPORTING"),
        "requiredForGoal": action_doc.get("requiredForGoal", True),
        "currentSubGoal": action_doc.get("currentSubGoal"),
        "goalAlignmentScore": action_doc.get("goalAlignmentScore", 100),
        "riskLevel": action_doc.get("riskLevel", "LOW"),
        "riskScore": action_doc.get("riskScore", 0),
        "driftScore": action_doc.get("driftScore", 0),
        "driftLevel": action_doc.get("driftLevel", "NORMAL"),
        "actionClassification": action_doc.get("actionClassification", "PRODUCTIVE"),
        "reason": action_doc.get("reason", "Gateway evaluated action."),
    }


@router.get("/status")
async def get_agent_status():
    """Check Antigravity agent connection status."""
    status = await get_antigravity_connection_status()
    return status


@router.post("/session/bind")
async def bind_agent_session(req: SessionBindRequest):
    """Manually bind an active Antigravity session/conversation to a goal."""
    res = await bind_session(req.conversationId, req.goalId, req.agent)
    return {"status": "bound", "session": res}


class ConnectRequest(BaseModel):
    sessionId: Optional[str] = None
    conversationId: Optional[str] = None


@router.post("/connect")
@router.post("/session/connect")
async def connect_agent(req: Optional[ConnectRequest] = None):
    """Connect/reactivate active Antigravity session."""
    from app.services.session_service import connect_antigravity_session
    session_id = req.sessionId if req else None
    conversation_id = req.conversationId if req else None
    result = await connect_antigravity_session(session_id, conversation_id)
    return result


class DisconnectRequest(BaseModel):
    sessionId: Optional[str] = None
    conversationId: Optional[str] = None


@router.post("/disconnect")
@router.post("/session/disconnect")
async def disconnect_agent(req: Optional[DisconnectRequest] = None):
    """Disconnect active Antigravity session without deleting historical data."""
    from app.services.session_service import disconnect_antigravity_session
    session_id = req.sessionId if req else None
    conversation_id = req.conversationId if req else None
    result = await disconnect_antigravity_session(session_id, conversation_id)
    return result

