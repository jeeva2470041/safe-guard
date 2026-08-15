"""
Pydantic schemas for request/response validation.
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


# ─── Goal Schemas ───────────────────────────────────────────────

class GoalCreate(BaseModel):
    """Request body for creating a new goal."""
    userGoal: str = Field(..., description="The user's goal description")
    constraints: List[str] = Field(
        default_factory=list,
        description="Optional constraints for the agent"
    )
    goalPolicy: Optional[dict] = Field(
        default=None,
        description="Optional pre-analyzed dynamic goal policy"
    )


class GoalModifyRequest(BaseModel):
    """Request body for modifying an active or paused goal."""
    userGoal: str = Field(..., description="The updated goal description")
    constraints: List[str] = Field(
        default_factory=list,
        description="Updated constraints"
    )
    changeReason: Optional[str] = Field(
        default="User intentional scope change",
        description="Reason for updating the goal"
    )


class GoalVersionEntry(BaseModel):
    """Entry for goal version history."""
    version: int
    userGoal: str
    constraints: List[str]
    goalPolicy: Optional[dict] = None
    createdAt: str
    changeReason: Optional[str] = None
    status: str = "COMPLETED"


class GoalResponse(BaseModel):
    """Full goal document response."""
    goalId: str
    userGoal: str
    constraints: List[str]
    status: str
    goalVersion: int = 1
    goalPolicy: Optional[dict] = None
    pauseReason: Optional[str] = None
    createdAt: str


# ─── Session Schemas ────────────────────────────────────────────

class SessionStartRequest(BaseModel):
    """Request payload for starting/updating an agent session via PreInvocation hook."""
    conversationId: str = Field(..., description="Unique Antigravity conversation ID")
    sessionId: Optional[str] = Field(default=None, description="Optional session ID alias")
    userPrompt: str = Field(..., description="Natural language prompt entered into Antigravity")
    workspacePaths: Optional[List[str]] = Field(default_factory=list, description="Active workspace paths")
    invocationNum: Optional[int] = Field(default=1, description="Invocation turn count")
    agent: Optional[str] = Field(default="antigravity", description="Agent identifier")


class SessionStartResponse(BaseModel):
    """Response returned when an agent session is registered/updated."""
    conversationId: str
    sessionId: str
    goalId: str
    goalVersion: int
    userGoal: str
    goalPolicy: dict
    status: str
    isNewGoal: bool = False
    isVersionUpdate: bool = False


# ─── Action Schemas ─────────────────────────────────────────────

class ActionResponse(BaseModel):
    """Full action document response."""
    actionId: str
    goalId: str
    goalVersion: int = 1
    agentId: str
    actionType: str
    description: str
    target: str
    goalAlignmentScore: int
    alignmentScore: Optional[int] = None
    alignmentStatus: str
    driftScore: int = 0
    driftLevel: str = "NORMAL"
    driftDetected: bool = False
    rollingIntegrity: float = 100.0
    violatedConstraints: List[str] = Field(default_factory=list)
    scopeViolation: bool = False
    riskLevel: str
    riskScore: int
    cumulativeRiskScore: int = 0
    cumulativeRiskLevel: str = "LOW"
    actionClassification: str = "PRODUCTIVE"
    decision: str
    reason: str
    executionStatus: str
    verificationStatus: Optional[str] = None
    verificationMessage: Optional[str] = None
    pauseTriggered: bool = False
    pauseReason: Optional[str] = None
    timestamp: str


# ─── Dashboard & Behavior Schemas ───────────────────────────────

class TrendDataPoint(BaseModel):
    actionNumber: int
    actionType: str
    target: str
    alignmentScore: int
    rollingIntegrity: float
    driftScore: int
    cumulativeRiskScore: int
    decision: str


class AgentBehaviorSummary(BaseModel):
    totalActions: int = 0
    aligned: int = 0
    partiallyAligned: int = 0
    unaligned: int = 0
    blocked: int = 0
    approvalRequired: int = 0
    goalViolations: int = 0
    sensitiveOperationsAttempted: int = 0
    currentDriftLevel: str = "NORMAL"
    currentDriftScore: int = 0
    cumulativeRiskLevel: str = "LOW"
    cumulativeRiskScore: int = 0
    agentSafetyScore: int = 100


class DashboardResponse(BaseModel):
    """Aggregated statistics for the V5 dashboard."""
    totalActions: int = 0
    allowedActions: int = 0
    blockedActions: int = 0
    pendingActions: int = 0
    approvedActions: int = 0
    rejectedActions: int = 0
    highRiskActions: int = 0
    goalIntegrityScore: float = 100.0
    overallGoalIntegrity: float = 100.0
    currentActionAlignment: int = 100
    currentDriftScore: int = 0
    currentDriftLevel: str = "NORMAL"
    cumulativeRiskScore: int = 0
    cumulativeRiskLevel: str = "LOW"
    agentSafetyScore: int = 100
    agentStatus: str = "IDLE"
    pauseReason: Optional[str] = None
    recentDivergentAction: Optional[str] = None
    dangerousActionsPrevented: int = 0
    goalVersion: int = 1
    trendData: List[TrendDataPoint] = Field(default_factory=list)
    behaviorSummary: Optional[AgentBehaviorSummary] = None


# ─── Audit Log Schemas ─────────────────────────────────────────

class AuditLogEntry(BaseModel):
    """Audit log entry for security decisions."""
    logId: str
    goalId: str
    actionId: str
    decision: str
    riskLevel: str
    reason: str
    timestamp: str
