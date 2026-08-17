from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum

class HealthStatus(str, Enum):
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    UNHEALTHY = "UNHEALTHY"

class SpanContext(BaseModel):
    trace_id: str
    span_id: str
    parent_span_id: Optional[str] = None
    correlation_id: str

class TraceSpanVO(BaseModel):
    span_id: str
    name: str
    parent_span_id: Optional[str] = None
    status: str
    start_time: datetime
    end_time: Optional[datetime] = None
    attributes: Dict[str, Any] = Field(default_factory=dict)

class TraceTree(BaseModel):
    trace_id: str
    correlation_id: str
    root_span_id: Optional[str] = None
    spans: Dict[str, TraceSpanVO] = Field(default_factory=dict)

class TimelineEvent(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    name: str
    description: str
    module: str  # planner, runtime, knowledge, approval, connector, ai, execution
    context_info: Dict[str, Any] = Field(default_factory=dict)

class Metric(BaseModel):
    name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    value: float
    labels: Dict[str, str] = Field(default_factory=dict)

class CounterMetric(Metric):
    pass

class GaugeMetric(Metric):
    pass

class HistogramMetric(Metric):
    count: int
    sum: float
    buckets: Dict[float, int] = Field(default_factory=dict)

class AlertCondition(BaseModel):
    metric_name: str
    operator: str  # GREATER_THAN, LESS_THAN, EQUAL
    threshold: float
    duration_seconds: int = 60

class AlertRule(BaseModel):
    rule_id: str
    name: str
    condition: AlertCondition
    severity: str = "WARNING"  # INFO, WARNING, CRITICAL

class AlertPolicy(BaseModel):
    policy_id: str
    name: str
    rules: List[AlertRule] = Field(default_factory=list)
    is_enabled: bool = True

class ServiceStatus(BaseModel):
    name: str
    status: HealthStatus
    message: Optional[str] = None
    last_checked: datetime = Field(default_factory=datetime.utcnow)

class ConnectorHealth(BaseModel):
    connector_id: str
    status: HealthStatus
    latency_ms: float
    last_checked: datetime = Field(default_factory=datetime.utcnow)

class PlannerHealth(BaseModel):
    status: HealthStatus
    avg_planning_time_ms: float
    success_rate: float
    last_checked: datetime = Field(default_factory=datetime.utcnow)

class RuntimeHealth(BaseModel):
    status: HealthStatus
    active_sessions: int
    concurrency_utilization: float
    last_checked: datetime = Field(default_factory=datetime.utcnow)

class KnowledgeHealth(BaseModel):
    status: HealthStatus
    avg_retrieval_latency_ms: float
    cache_hit_ratio: float
    last_checked: datetime = Field(default_factory=datetime.utcnow)

class ApprovalHealth(BaseModel):
    status: HealthStatus
    pending_count: int
    avg_approval_delay_seconds: float
    last_checked: datetime = Field(default_factory=datetime.utcnow)

class AIGatewayHealth(BaseModel):
    status: HealthStatus
    active_providers_count: int
    failed_requests_last_hour: int
    last_checked: datetime = Field(default_factory=datetime.utcnow)

class CostMetric(BaseModel):
    model_name: str
    input_tokens: int = 0
    output_tokens: int = 0
    estimated_cost: float = 0.0

class LatencyMetric(BaseModel):
    operation_name: str
    duration_ms: float

class UsageMetric(BaseModel):
    operation_name: str
    success_count: int = 0
    error_count: int = 0

class ErrorMetric(BaseModel):
    operation_name: str
    error_code: str
    error_message: str

class SlaMetric(BaseModel):
    workflow_id: str
    sla_threshold_seconds: float
    actual_duration_seconds: float
    is_breached: bool = False

class ObservabilityStatistics(BaseModel):
    total_traces: int = 0
    total_logs: int = 0
    total_alerts: int = 0
    total_cost: float = 0.0
    average_latency_ms: float = 0.0
    error_rate: float = 0.0

class TelemetryEvent(BaseModel):
    event_id: str
    event_type: str
    timestamp: datetime
    org_id: str
    correlation_id: str
    payload: Dict[str, Any] = Field(default_factory=dict)
