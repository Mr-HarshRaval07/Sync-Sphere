from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List

class CreateApprovalCommand(BaseModel):
    org_id: str
    title: str
    context: Dict[str, Any] = Field(default_factory=dict)
    workflow_id: Optional[str] = None
    node_id: Optional[str] = None
    session_id: Optional[str] = None
    description: Optional[str] = None
    template_id: Optional[str] = None
    correlation_id: Optional[str] = None

class ApproveCommand(BaseModel):
    org_id: str
    approval_id: str
    user_id: str
    comment: Optional[str] = None
    correlation_id: Optional[str] = None

class RejectCommand(BaseModel):
    org_id: str
    approval_id: str
    user_id: str
    comment: Optional[str] = None
    correlation_id: Optional[str] = None

class DelegateCommand(BaseModel):
    org_id: str
    approval_id: str
    from_user_id: str
    to_user_id: str
    reason: Optional[str] = None
    correlation_id: Optional[str] = None

class EscalateCommand(BaseModel):
    org_id: str
    approval_id: str
    level: int
    assigned_role_id: Optional[str] = None
    assigned_user_id: Optional[str] = None
    reason: Optional[str] = None
    correlation_id: Optional[str] = None

class CancelApprovalCommand(BaseModel):
    org_id: str
    approval_id: str
    correlation_id: Optional[str] = None

class AddCommentCommand(BaseModel):
    org_id: str
    approval_id: str
    user_id: str
    text: str
    correlation_id: Optional[str] = None
