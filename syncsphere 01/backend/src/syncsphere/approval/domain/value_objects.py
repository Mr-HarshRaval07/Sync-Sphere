from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class ApprovalDecisionType(str, Enum):
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    DELEGATE = "DELEGATE"
    ESCALATE = "ESCALATE"
    PENDING = "PENDING"

class RoutingStrategyType(str, Enum):
    SEQUENTIAL = "SEQUENTIAL"
    PARALLEL = "PARALLEL"
    CONSENSUS = "CONSENSUS"
    MAJORITY = "MAJORITY"
    FIRST_RESPONSE = "FIRST_RESPONSE"
    WEIGHTED = "WEIGHTED"
    CUSTOM = "CUSTOM"

class DelegationType(str, Enum):
    TEMPORARY = "TEMPORARY"
    PERMANENT = "PERMANENT"
    OUT_OF_OFFICE = "OUT_OF_OFFICE"
    AUTOMATIC = "AUTOMATIC"

class ApprovalPolicyType(str, Enum):
    ROLE_BASED = "ROLE_BASED"
    ORGANIZATION = "ORGANIZATION"
    RISK_BASED = "RISK_BASED"
    COST_BASED = "COST_BASED"
    WORKFLOW = "WORKFLOW"
    RESOURCE = "RESOURCE"
    CONNECTOR = "CONNECTOR"
    SENSITIVE_OPERATION = "SENSITIVE_OPERATION"

class ApprovalAssignment(BaseModel):
    user_id: Optional[str] = None
    role_id: Optional[str] = None
    team_id: Optional[str] = None
    dynamic_resolver: Optional[str] = None  # manager, direct_supervisor
    weight: float = 1.0
    is_delegated: bool = False
    original_assignee_id: Optional[str] = None

class ApprovalDecision(BaseModel):
    user_id: str
    decision: ApprovalDecisionType
    comment: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ApprovalStage(BaseModel):
    stage_id: str
    name: str
    order: int
    routing_strategy: RoutingStrategyType
    assignments: List[ApprovalAssignment]
    decisions: List[ApprovalDecision] = Field(default_factory=list)
    status: str = "PENDING"  # PENDING, ACTIVE, COMPLETED, REJECTED, ESCALATED

class ApprovalChain(BaseModel):
    stages: List[ApprovalStage] = Field(default_factory=list)
    current_stage_index: int = 0

    def get_current_stage(self) -> Optional[ApprovalStage]:
        if 0 <= self.current_stage_index < len(self.stages):
            return self.stages[self.current_stage_index]
        return None

class ApprovalCondition(BaseModel):
    left_operand: str
    operator: str  # EQUAL, GREATER_THAN, LESS_THAN, CONTAINS
    right_operand: Any

class ApprovalRule(BaseModel):
    rule_id: str
    name: str
    policy_type: ApprovalPolicyType
    conditions: List[ApprovalCondition] = Field(default_factory=list)
    cost_threshold: Optional[float] = None
    risk_threshold: Optional[str] = None  # LOW, MEDIUM, HIGH

class ApprovalSLA(BaseModel):
    duration_seconds: int
    remaining_seconds: Optional[float] = None
    is_overdue: bool = False
    breached_at: Optional[datetime] = None

class ApprovalEscalation(BaseModel):
    escalation_level: int
    assigned_role_id: Optional[str] = None
    assigned_user_id: Optional[str] = None
    escalated_at: Optional[datetime] = None
    escalation_reason: Optional[str] = None

class ApprovalReminder(BaseModel):
    interval_seconds: int
    last_sent_at: Optional[datetime] = None
    next_due_at: Optional[datetime] = None

class ApprovalComment(BaseModel):
    comment_id: str
    user_id: str
    text: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ApprovalHistory(BaseModel):
    history_id: str
    action: str  # Created, Assigned, Approved, Rejected, Delegated, Escalated, Commented
    user_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    details: Dict[str, Any] = Field(default_factory=dict)

class ApprovalContext(BaseModel):
    variables: Dict[str, Any] = Field(default_factory=dict)
    operation_name: Optional[str] = None
    cost: Optional[float] = None
    risk_level: Optional[str] = "LOW"
    creator_id: Optional[str] = None
    workflow_id: Optional[str] = None

class ApprovalMetrics(BaseModel):
    average_duration_seconds: float = 0.0
    sla_compliance_percentage: float = 100.0
    escalation_count: int = 0
    approver_workloads: Dict[str, int] = Field(default_factory=dict)
    stage_bottlenecks: Dict[str, float] = Field(default_factory=dict)

class ApprovalStatistics(BaseModel):
    total_requests: int = 0
    pending_count: int = 0
    approved_count: int = 0
    rejected_count: int = 0
    metrics: ApprovalMetrics = Field(default_factory=ApprovalMetrics)
