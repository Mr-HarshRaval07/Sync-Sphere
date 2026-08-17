from typing import List, Optional
from syncsphere.core.events.base import BaseEvent

class ApprovalCreated(BaseEvent):
    event_type: str = "approval.created"
    approval_id: str
    org_id: str

class ApprovalAssigned(BaseEvent):
    event_type: str = "approval.assigned"
    approval_id: str
    org_id: str
    stage_id: str
    assignee_ids: List[str]

class ApprovalRequested(BaseEvent):
    event_type: str = "approval.requested"
    approval_id: str
    org_id: str
    stage_id: str
    assignee_ids: List[str]

class ApprovalDelegated(BaseEvent):
    event_type: str = "approval.delegated"
    approval_id: str
    org_id: str
    from_user_id: str
    to_user_id: str
    reason: Optional[str] = None

class ApprovalEscalated(BaseEvent):
    event_type: str = "approval.escalated"
    approval_id: str
    org_id: str
    escalation_level: int
    assigned_user_id: Optional[str] = None
    assigned_role_id: Optional[str] = None

class ApprovalReminderSent(BaseEvent):
    event_type: str = "approval.reminder_sent"
    approval_id: str
    org_id: str
    user_ids: List[str]

class ApprovalApproved(BaseEvent):
    event_type: str = "approval.approved"
    approval_id: str
    org_id: str
    decision_maker_id: str

class ApprovalRejected(BaseEvent):
    event_type: str = "approval.rejected"
    approval_id: str
    org_id: str
    decision_maker_id: str

class ApprovalTimedOut(BaseEvent):
    event_type: str = "approval.timed_out"
    approval_id: str
    org_id: str

class ApprovalCompleted(BaseEvent):
    event_type: str = "approval.completed"
    approval_id: str
    org_id: str
    approved: bool
    session_id: Optional[str] = None
    node_id: Optional[str] = None

class ApprovalCancelled(BaseEvent):
    event_type: str = "approval.cancelled"
    approval_id: str
    org_id: str
