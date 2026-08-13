from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from syncsphere.approval.domain.value_objects import ApprovalChain, ApprovalSLA, ApprovalStatistics

class CreateApprovalRequest(BaseModel):
    title: str = Field(..., min_length=1)
    context: Dict[str, Any] = Field(default_factory=dict)
    workflow_id: Optional[str] = None
    node_id: Optional[str] = None
    session_id: Optional[str] = None
    description: Optional[str] = None
    template_id: Optional[str] = None

class SubmitDecisionRequest(BaseModel):
    comment: Optional[str] = None

class DelegateRequest(BaseModel):
    to_user_id: str = Field(..., min_length=1)
    reason: Optional[str] = None

class AddCommentRequest(BaseModel):
    text: str = Field(..., min_length=1)

class ApprovalResponse(BaseModel):
    id: str
    org_id: str
    title: str
    description: Optional[str] = None
    status: str
    context: Dict[str, Any] = Field(default_factory=dict)
    workflow_id: Optional[str] = None
    node_id: Optional[str] = None
    chain: ApprovalChain
    sla: Optional[ApprovalSLA] = None
    escalation_count: int = 0
    version: int = 1
    created_at: datetime
    completed_at: Optional[datetime] = None
