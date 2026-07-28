from pydantic import BaseModel, Field
from typing import Dict, Any, Optional

class StartExecutionCommand(BaseModel):
    org_id: str
    workflow_id: str
    version: Optional[int] = None
    inputs: Dict[str, Any] = Field(default_factory=dict)
    policy: str = "BalancedExecution"
    correlation_id: Optional[str] = None

class PauseExecutionCommand(BaseModel):
    org_id: str
    session_id: str
    correlation_id: Optional[str] = None

class ResumeExecutionCommand(BaseModel):
    org_id: str
    session_id: str
    correlation_id: Optional[str] = None

class CancelExecutionCommand(BaseModel):
    org_id: str
    session_id: str
    correlation_id: Optional[str] = None

class RetryExecutionCommand(BaseModel):
    org_id: str
    session_id: str
    correlation_id: Optional[str] = None

class ApproveExecutionCommand(BaseModel):
    org_id: str
    session_id: str
    node_id: str
    approved: bool
    correlation_id: Optional[str] = None
