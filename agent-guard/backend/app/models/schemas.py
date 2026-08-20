"""
Pydantic schemas for request/response validation.
Supports Phase 1: Intent-Preserving Runtime Security Gateway with formal User Intent Model.
Supports Phase 2: Real-World Action Authorization, External Context Trust, and Contextual Human Approval.
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from enum import Enum
from datetime import datetime


# ─── Enums ────────────────────────────────────────────────────

class ConsequenceLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ExternalContentType(str, Enum):
    INFORMATION = "INFORMATION"
    INSTRUCTION = "INSTRUCTION"


class ApprovalMode(str, Enum):
    ONCE = "ONCE"
    SIMILAR = "SIMILAR"
    REJECT = "REJECT"
    ABORT = "ABORT"


# ─── User Intent & Authority Schemas ──────────────────────────

class SubGoal(BaseModel):
    """Structured sub-goal node within a hierarchical goal representation."""
    id: str = Field(..., description="Unique sub-goal identifier (e.g. SG-1)")
    name: str = Field(..., description="Short name of the sub-goal")
    description: Optional[str] = Field(default="", description="Detailed objective of this sub-goal")
    order: int = Field(default=1, description="Execution sequence position")
    status: str = Field(default="PENDING", description="PENDING | ACTIVE | COMPLETED | SKIPPED")
    allowedActions: List[str] = Field(default_factory=list, description="Action types permitted for this sub-goal")


class FinancialAuthority(BaseModel):
    """Defines monetary authorization boundaries for the agent."""
    authorized: bool = Field(default=False, description="Whether financial transactions are permitted")
    maxAmount: float = Field(default=0.0, description="Maximum automated transaction limit")
    currency: str = Field(default="INR", description="Currency symbol or ISO code")
    requiresApproval: bool = Field(default=True, description="Whether human approval is mandated for payment")


class ExternalCommunicationAuthority(BaseModel):
    """Defines external communication permissions (email, webhook, messaging)."""
    authorized: bool = Field(default=False, description="Whether external communication is permitted")
    allowedRecipients: List[str] = Field(default_factory=list, description="Explicit authorized recipient addresses or domains")
    requiresApproval: bool = Field(default=True, description="Whether sending communication requires human confirmation")


class PersonalDataAuthority(BaseModel):
    """Defines user data and PII access limits."""
    authorized: bool = Field(default=True, description="Whether standard user data autofill is permitted")
    allowedFields: List[str] = Field(default_factory=list, description="Permitted fields (e.g. name, email, phone)")
    requiresApprovalForSensitive: bool = Field(default=True, description="Whether sensitive data/PII requires human review")


class UserIntentModel(BaseModel):
    """
    Formal User Intent Model — represents the user's overarching intent,
    authorized boundaries, authorities, entities, and hierarchical sub-goals.
    """
    original_goal: str = Field(..., description="The user's original natural-language prompt")
    objective: str = Field(..., description="Normalized high-level functional objective")
    entities: Dict[str, Any] = Field(default_factory=dict, description="Extracted domain entities (origin, destination, budget, etc.)")
    desired_outcome: str = Field(default="", description="Description of the successful end state")
    constraints: List[str] = Field(default_factory=list, description="Positive and operational constraints")
    negative_constraints: List[str] = Field(default_factory=list, description="Explicit negative safety boundaries")
    allowed_domains: List[str] = Field(default_factory=list, description="Authorized web domains, services, or repository layers")
    allowed_action_categories: List[str] = Field(default_factory=list, description="Permitted action categories (SEARCH, BROWSE, etc.)")
    sensitive_action_categories: List[str] = Field(default_factory=list, description="Categories requiring human review (PAYMENT, etc.)")
    forbidden_action_categories: List[str] = Field(default_factory=list, description="Strictly prohibited action categories")
    financial_authority: FinancialAuthority = Field(default_factory=FinancialAuthority)
    external_communication_authority: ExternalCommunicationAuthority = Field(default_factory=ExternalCommunicationAuthority)
    personal_data_authority: PersonalDataAuthority = Field(default_factory=PersonalDataAuthority)
    goal_version: int = Field(default=1, description="Intent policy version")
    sub_goals: List[SubGoal] = Field(default_factory=list, description="Hierarchical sub-goals")

    # Backward-compatible fields for V4/V5 policy consumers
    domain: Optional[str] = "general software development"
    technologies: List[str] = Field(default_factory=list)
    requirements: List[str] = Field(default_factory=list)
    allowedScope: List[str] = Field(default_factory=list)
    restrictedScope: List[str] = Field(default_factory=list)
    sensitiveOperations: List[str] = Field(default_factory=list)
    isAmbiguous: bool = False


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
        description="Optional pre-analyzed dynamic goal policy / User Intent Model"
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

class ApproveActionRequest(BaseModel):
    """Request body for approving/rejecting an action with approvalMode."""
    approvalMode: str = Field(default="ONCE", description="ONCE | SIMILAR | REJECT | ABORT")
    reason: Optional[str] = Field(default="Approved by user", description="Human reason for decision")


class ActionResponse(BaseModel):
    """Full action document response with Phase 1 & 2 Intent Forensics."""
    actionId: str
    goalId: str
    goalVersion: int = 1
    agentId: str
    actionType: str
    description: str
    target: str

    # Phase 1 & 2: Action-to-Goal Relationship & Forensics
    source: str = "USER"  # USER | SYSTEM | AGENT_PLAN | TRUSTED_TOOL | WEBSITE | DOCUMENT | EMAIL | SEARCH_RESULT | API_RESPONSE | MCP_TOOL | UNKNOWN
    purpose: Optional[str] = None
    goalRelationship: str = "DIRECTLY_RELEVANT"  # DIRECTLY_RELEVANT | SUPPORTING | INDIRECTLY_RELEVANT | UNRELATED | CONTRADICTORY
    goal_relationship: Optional[str] = None
    requiredForGoal: bool = True
    required_for_goal: Optional[bool] = None
    consequence: Optional[str] = None
    consequenceLevel: str = "LOW"  # LOW | MEDIUM | HIGH | CRITICAL
    reversibility: str = "REVERSIBLE"  # REVERSIBLE | PARTIALLY_REVERSIBLE | IRREVERSIBLE
    currentSubGoal: Optional[str] = None
    current_sub_goal: Optional[str] = None
    sourceTrustLevel: str = "TRUSTED"  # TRUSTED | SEMI_TRUSTED | UNTRUSTED

    # Integrity & Drift Forensics
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


# ─── External Context & Instruction Evaluation Schemas ─────────

class EvaluateInstructionRequest(BaseModel):
    """Request to evaluate an external content / instruction from a website/PDF/email/API."""
    goalId: Optional[str] = None
    userGoal: Optional[str] = None
    content: str = Field(..., description="Raw text or instruction received from external source")
    source: str = Field(default="WEBSITE", description="WEBSITE | PDF | EMAIL | SEARCH_RESULT | API_RESPONSE | DOCUMENT | MCP_RESULT")
    proposedActionType: Optional[str] = None
    proposedTarget: Optional[str] = None


class EvaluateInstructionResponse(BaseModel):
    """Result of external content evaluation."""
    contentType: str = "INFORMATION"  # INFORMATION | INSTRUCTION
    goalRelationship: str = "SUPPORTING"  # DIRECTLY_RELEVANT | SUPPORTING | INDIRECTLY_RELEVANT | UNRELATED | CONTRADICTORY
    consequenceLevel: str = "LOW"  # LOW | MEDIUM | HIGH | CRITICAL
    riskLevel: str = "LOW"  # LOW | MEDIUM | HIGH | CRITICAL
    riskScore: int = 10
    decision: str = "ALLOW"  # ALLOW | REQUIRE_APPROVAL | BLOCK
    reason: str
    isGoalChanging: bool = False
    canContinueWorkflow: bool = True


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
    """Aggregated statistics for the dashboard."""
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


# ─── Phase 3: Attack Detection & Incident Schemas ───────────────

class AttackChainNode(BaseModel):
    nodeId: str
    actionId: str
    actionType: str
    target: str
    decision: str
    riskLevel: str
    roleInAttack: str
    timestamp: str


class AttackChainEdge(BaseModel):
    fromNode: str = Field(..., alias="from")
    toNode: str = Field(..., alias="to")
    relation: str


class AttackChainSchema(BaseModel):
    attackType: str
    goalId: str
    severity: str
    nodeCount: int
    nodes: List[AttackChainNode] = Field(default_factory=list)
    edges: List[Dict[str, Any]] = Field(default_factory=list)
    evidence: List[str] = Field(default_factory=list)
    createdAt: str


class IncidentRecord(BaseModel):
    incidentId: str
    goalId: str
    attackType: str
    severity: str
    status: str = "OPEN"
    actionId: str
    actionType: str
    target: str
    triggerReason: str
    evidence: List[str] = Field(default_factory=list)
    attackChain: Optional[Dict[str, Any]] = None
    containmentAction: str = "AGENT_FROZEN"
    createdAt: str
    updatedAt: str

