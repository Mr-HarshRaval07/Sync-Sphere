from pydantic import Field
from syncsphere.core.events.base import BaseEvent

class ExecutionStarted(BaseEvent):
    event_type: str = "runtime.execution_started"
    session_id: str

class ExecutionPaused(BaseEvent):
    event_type: str = "runtime.execution_paused"
    session_id: str

class ExecutionResumed(BaseEvent):
    event_type: str = "runtime.execution_resumed"
    session_id: str

class ExecutionCompleted(BaseEvent):
    event_type: str = "runtime.execution_completed"
    session_id: str

class ExecutionFailed(BaseEvent):
    event_type: str = "runtime.execution_failed"
    session_id: str
    error_message: str

class ExecutionRetried(BaseEvent):
    event_type: str = "runtime.execution_retried"
    session_id: str
    node_id: str
    attempt: int

class ExecutionCancelled(BaseEvent):
    event_type: str = "runtime.execution_cancelled"
    session_id: str

class CheckpointCreated(BaseEvent):
    event_type: str = "runtime.checkpoint_created"
    session_id: str
    checkpoint_id: str

class CheckpointRestored(BaseEvent):
    event_type: str = "runtime.checkpoint_restored"
    session_id: str
    checkpoint_id: str

class ApprovalRequested(BaseEvent):
    event_type: str = "runtime.approval_requested"
    session_id: str
    node_id: str
    approver_role_id: str

class ApprovalReceived(BaseEvent):
    event_type: str = "runtime.approval_received"
    session_id: str
    node_id: str
    approved: bool

class CompensationStarted(BaseEvent):
    event_type: str = "runtime.compensation_started"
    session_id: str

class CompensationCompleted(BaseEvent):
    event_type: str = "runtime.compensation_completed"
    session_id: str

class WorkerAssigned(BaseEvent):
    event_type: str = "runtime.worker_assigned"
    session_id: str
    worker_id: str

class WorkerReleased(BaseEvent):
    event_type: str = "runtime.worker_released"
    session_id: str
    worker_id: str
