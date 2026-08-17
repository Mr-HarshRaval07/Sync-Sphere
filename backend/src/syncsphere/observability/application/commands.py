from pydantic import BaseModel
from typing import Optional, Dict, Any

class CreateAlertCommand(BaseModel):
    org_id: str
    name: str
    message: str
    severity: str = "WARNING"
    metric_name: Optional[str] = None

class ResolveAlertCommand(BaseModel):
    org_id: str
    alert_id: str

class StartReplayCommand(BaseModel):
    org_id: str
    session_id: str
    replay_type: str = "execution"  # execution, workflow, planner

class ExportReplayCommand(BaseModel):
    org_id: str
    replay_id: str
    export_format: str = "json"  # json, csv

class RefreshMetricsCommand(BaseModel):
    org_id: str
