from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime

class StartExecutionRequest(BaseModel):
    workflow_id: str
    version: Optional[int] = None
    inputs: Dict[str, Any] = Field(default_factory=dict)
    policy: str = "BalancedExecution"

class StartExecutionResponse(BaseModel):
    session_id: str
    status: str
    workflow_id: str
    version: int

class PauseExecutionRequest(BaseModel):
    session_id: str

class ResumeExecutionRequest(BaseModel):
    session_id: str

class CancelExecutionRequest(BaseModel):
    session_id: str

class RetryExecutionRequest(BaseModel):
    session_id: str

class ApproveExecutionRequest(BaseModel):
    session_id: str
    node_id: str
    approved: bool

class StepStatusResponse(BaseModel):
    node_id: str
    name: str
    type: str
    status: str
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    retries_attempted: int = 0

class ExecutionStatusResponse(BaseModel):
    session_id: str
    workflow_id: str
    version: int
    status: str
    variables: Dict[str, Any] = Field(default_factory=dict)
    steps: Dict[str, StepStatusResponse] = Field(default_factory=dict)
    error_message: Optional[str] = None

class TimelineEvent(BaseModel):
    timestamp: str
    action: str
    details: Dict[str, Any] = Field(default_factory=dict)

class ExecutionTimelineResponse(BaseModel):
    session_id: str
    events: List[TimelineEvent] = Field(default_factory=list)

class ExecutionMetricsResponse(BaseModel):
    session_id: str
    total_execution_time_ms: float
    steps_completed: int
    steps_failed: int
    retry_count: int
