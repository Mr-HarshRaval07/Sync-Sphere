from pydantic import BaseModel
from typing import Optional

class ExecutionStatusQuery(BaseModel):
    org_id: str
    session_id: str

class ExecutionHistoryQuery(BaseModel):
    org_id: str
    session_id: str

class ExecutionMetricsQuery(BaseModel):
    org_id: str
    session_id: str

class ExecutionLogsQuery(BaseModel):
    org_id: str
    session_id: str

class ExecutionTimelineQuery(BaseModel):
    org_id: str
    session_id: str

class ExecutionTraceQuery(BaseModel):
    org_id: str
    session_id: str
