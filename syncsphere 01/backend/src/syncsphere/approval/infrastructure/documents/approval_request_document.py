from datetime import datetime
from typing import List, Optional
from pydantic import Field
from syncsphere.shared_kernel.infrastructure.mongodb.base_document import BaseTenantDocument
from syncsphere.approval.domain.value_objects import (
    ApprovalChain,
    ApprovalSLA,
    ApprovalEscalation,
    ApprovalReminder,
    ApprovalComment,
    ApprovalHistory
)

class ApprovalRequestDocument(BaseTenantDocument):
    title: str = Field(..., description="Short title describing approval intent")
    chain: ApprovalChain = Field(..., description="Approval stages and assignee decision logs")
    workflow_id: Optional[str] = None
    node_id: Optional[str] = None
    session_id: Optional[str] = None
    description: Optional[str] = None
    status: str = Field(default="PENDING")
    sla: Optional[ApprovalSLA] = None
    escalation_policy: List[ApprovalEscalation] = Field(default_factory=list)
    reminder_policy: Optional[ApprovalReminder] = None
    comments: List[ApprovalComment] = Field(default_factory=list)
    history: List[ApprovalHistory] = Field(default_factory=list)
    version: int = 1
    completed_at: Optional[datetime] = None
    escalation_count: int = 0

    class Settings:
        name = "approval_requests"
        indexes = [
            "org_id",
            "status",
            "workflow_id",
            "session_id",
            "created_at"
        ]
