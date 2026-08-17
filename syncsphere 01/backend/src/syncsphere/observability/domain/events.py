from pydantic import Field
from typing import Dict, Any, Optional
from datetime import datetime
from syncsphere.core.events.base import BaseEvent

class AlertRaised(BaseEvent):
    event_type: str = "observability.alert_raised"
    alert_id: str
    name: str
    message: str
    severity: str

class AlertResolved(BaseEvent):
    event_type: str = "observability.alert_resolved"
    alert_id: str
    name: str
    resolved_at: datetime

class ReplayCreated(BaseEvent):
    event_type: str = "observability.replay_created"
    replay_id: str
    session_id: str
    replay_type: str  # execution, workflow, planner

class HealthChanged(BaseEvent):
    event_type: str = "observability.health_changed"
    service_name: str
    old_status: str
    new_status: str

class MetricCollected(BaseEvent):
    event_type: str = "observability.metric_collected"
    metric_name: str
    value: float
    labels: Dict[str, str] = Field(default_factory=dict)

class TraceCompleted(BaseEvent):
    event_type: str = "observability.trace_completed"
    trace_id: str
    duration_ms: float
