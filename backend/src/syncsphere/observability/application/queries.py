from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class TraceDetailsQuery(BaseModel):
    org_id: str
    trace_id: str

class ExecutionTimelineQuery(BaseModel):
    org_id: str
    session_id: str

class WorkflowTimelineQuery(BaseModel):
    org_id: str
    workflow_id: str

class PlannerTimelineQuery(BaseModel):
    org_id: str
    planner_session_id: str

class MetricsDashboardQuery(BaseModel):
    org_id: str
    metric_name: str
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

class CostDashboardQuery(BaseModel):
    org_id: str
    user_id: str

class HealthDashboardQuery(BaseModel):
    org_id: str
    user_id: str

class AlertDashboardQuery(BaseModel):
    org_id: str
    status: Optional[str] = None  # ACTIVE, RESOLVED
