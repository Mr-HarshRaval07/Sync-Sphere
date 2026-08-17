from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class AlertCreateRequest(BaseModel):
    name: str = Field(..., example="High CPU Usage")
    message: str = Field(..., example="CPU exceeded 90% threshold")
    severity: str = Field(default="WARNING", example="CRITICAL")
    metric_name: Optional[str] = Field(default=None, example="system.cpu_utilization")

class ReplayStartRequest(BaseModel):
    session_id: str = Field(..., example="session-12345")
    replay_type: str = Field(default="execution", example="execution")  # execution, workflow, planner

class AlertResponse(BaseModel):
    alert_id: str
    name: str
    message: str
    severity: str
    status: str
    metric_name: Optional[str] = None
    created_at: str
    resolved_at: Optional[str] = None

class ReplayResponse(BaseModel):
    replay_id: str
    session_id: str
    replay_type: str
    timeline_events: List[Dict[str, Any]] = []

class TraceSpanResponse(BaseModel):
    span_id: str
    name: str
    parent_span_id: Optional[str] = None
    status: str
    start_time: str
    end_time: Optional[str] = None
    attributes: Dict[str, Any] = {}

class TraceResponse(BaseModel):
    trace_id: str
    org_id: str
    spans: List[TraceSpanResponse] = []
