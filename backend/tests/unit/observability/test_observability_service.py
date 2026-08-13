import pytest
from datetime import datetime, timedelta
from typing import List, Optional, Any, Dict

from syncsphere.observability.domain.entities.trace import Trace, TraceSpan
from syncsphere.observability.domain.entities.replay import ExecutionReplay, WorkflowReplay, PlannerReplay
from syncsphere.observability.domain.entities.log import StructuredLog
from syncsphere.observability.domain.entities.metric_series import MetricSeries
from syncsphere.observability.domain.entities.alert import Alert
from syncsphere.observability.domain.entities.health import HealthCheck
from syncsphere.observability.domain.entities.event_store import EventStoreEntry
from syncsphere.observability.domain.value_objects import (
    Metric, AlertPolicy, AlertRule, AlertCondition, HealthStatus, ServiceStatus
)
from unittest.mock import patch, MagicMock, AsyncMock

from syncsphere.observability.domain.repositories import (
    TraceRepository, ReplayRepository, MetricRepository, AlertRepository, HealthRepository, LogRepository, EventStoreRepository
)
from syncsphere.observability.application.services.tracing import DistributedTracer, TraceCollector
from syncsphere.observability.application.services.metrics import MetricsCollector
from syncsphere.observability.application.services.logging import StructuredLogger
from syncsphere.observability.application.services.alerting import AlertEngine
from syncsphere.observability.application.services.health import HealthAggregator, HealthReporter
from syncsphere.observability.application.services.analytics import AIAnalyticsEngine, ConnectorAnalyticsEngine
from syncsphere.observability.application.services.replay import (
    ExecutionReplayEngine, WorkflowReplayEngine, PlannerReplayEngine
)
from syncsphere.observability.application.services.event_store_service import EventStoreService

# --- In-Memory Mocks for Unit Testing ---

class InMemoryTraceRepository(TraceRepository):
    def __init__(self) -> None:
        self.traces: Dict[str, Trace] = {}

    async def save(self, trace: Trace) -> None:
        self.traces[trace.correlation_id] = trace

    async def get_by_correlation_id(self, org_id: str, correlation_id: str) -> Optional[Trace]:
        return self.traces.get(correlation_id)

    async def list_by_org(self, org_id: str, limit: int = 100) -> List[Trace]:
        return [t for t in self.traces.values() if t.org_id == org_id][:limit]

class InMemoryReplayRepository(ReplayRepository):
    def __init__(self) -> None:
        self.exe_replays: Dict[str, ExecutionReplay] = {}
        self.wf_replays: Dict[str, WorkflowReplay] = {}
        self.pl_replays: Dict[str, PlannerReplay] = {}

    async def save_execution_replay(self, replay: ExecutionReplay) -> None:
        self.exe_replays[replay.session_id] = replay

    async def get_execution_replay(self, org_id: str, session_id: str) -> Optional[ExecutionReplay]:
        return self.exe_replays.get(session_id)

    async def save_workflow_replay(self, replay: WorkflowReplay) -> None:
        self.wf_replays[replay.workflow_id] = replay

    async def get_workflow_replay(self, org_id: str, workflow_id: str) -> Optional[WorkflowReplay]:
        return self.wf_replays.get(workflow_id)

    async def save_planner_replay(self, replay: PlannerReplay) -> None:
        self.pl_replays[replay.planner_session_id] = replay

    async def get_planner_replay(self, org_id: str, planner_session_id: str) -> Optional[PlannerReplay]:
        return self.pl_replays.get(planner_session_id)

class InMemoryMetricRepository(MetricRepository):
    def __init__(self) -> None:
        self.series: Dict[str, MetricSeries] = {}

    async def save_series(self, series: MetricSeries) -> None:
        self.series[series.metric_name] = series

    async def get_series(self, org_id: str, metric_name: str, start_time: Optional[Any] = None, end_time: Optional[Any] = None) -> Optional[MetricSeries]:
        s = self.series.get(metric_name)
        if s and s.org_id == org_id:
            return s
        return None

    async def list_metric_names(self, org_id: str) -> List[str]:
        return [s.metric_name for s in self.series.values() if s.org_id == org_id]

class InMemoryAlertRepository(AlertRepository):
    def __init__(self) -> None:
        self.alerts: Dict[str, Alert] = {}

    async def save(self, alert: Alert) -> None:
        self.alerts[alert.id] = alert

    async def get_by_id(self, org_id: str, alert_id: str) -> Optional[Alert]:
        return self.alerts.get(alert_id)

    async def list_active(self, org_id: str) -> List[Alert]:
        return [a for a in self.alerts.values() if a.org_id == org_id and a.status == "ACTIVE"]

    async def list_all(self, org_id: str, limit: int = 100) -> List[Alert]:
        return [a for a in self.alerts.values() if a.org_id == org_id][:limit]

class InMemoryHealthRepository(HealthRepository):
    def __init__(self) -> None:
        self.checks: List[HealthCheck] = []

    async def save(self, check: HealthCheck) -> None:
        self.checks.append(check)

    async def get_latest(self, org_id: str) -> Optional[HealthCheck]:
        valid = [c for c in self.checks if c.org_id == org_id]
        return valid[-1] if valid else None

class InMemoryLogRepository(LogRepository):
    def __init__(self) -> None:
        self.logs: List[StructuredLog] = []

    async def save(self, log: StructuredLog) -> None:
        self.logs.append(log)

    async def list_logs(self, org_id: str, correlation_id: Optional[str] = None, level: Optional[str] = None, limit: int = 100) -> List[StructuredLog]:
        res = [l for l in self.logs if l.org_id == org_id]
        if correlation_id:
            res = [l for l in res if l.correlation_id == correlation_id]
        if level:
            res = [l for l in res if l.level == level]
        return res[:limit]

class InMemoryEventStoreRepository(EventStoreRepository):
    def __init__(self) -> None:
        self.events: List[EventStoreEntry] = []

    async def save(self, entry: EventStoreEntry) -> None:
        self.events.append(entry)

    async def get_by_id(self, org_id: str, event_id: str) -> Optional[EventStoreEntry]:
        for e in self.events:
            if e.org_id == org_id and e.event_id == event_id:
                return e
        return None

    async def search(self, org_id: str, event_type: Optional[str] = None, correlation_id: Optional[str] = None, limit: int = 100) -> List[EventStoreEntry]:
        res = [e for e in self.events if e.org_id == org_id]
        if event_type:
            res = [e for e in res if e.event_type == event_type]
        if correlation_id:
            res = [e for e in res if e.correlation_id == correlation_id]
        return res[:limit]


# --- Unit Tests Suite ---

@pytest.mark.asyncio
async def test_distributed_tracer_lifecycle():
    repo = InMemoryTraceRepository()
    tracer = DistributedTracer(repo)
    org_id = "org_1"
    correlation_id = "corr_123"

    # Start Span
    span = await tracer.start_span(org_id, "test.span", correlation_id)
    assert span.span_id is not None
    assert span.status == "RUNNING"

    # Complete Span
    await tracer.complete_span(org_id, correlation_id, span.span_id)
    trace = await repo.get_by_correlation_id(org_id, correlation_id)
    assert trace is not None
    assert len(trace.spans) == 1
    assert trace.spans[0].status == "COMPLETED"

@pytest.mark.asyncio
async def test_metrics_collector_and_rollups():
    repo = InMemoryMetricRepository()
    collector = MetricsCollector(repo)
    org_id = "org_1"

    # Record metrics
    m1 = collector.counter.increment("system.usage_total", 5.0)
    m2 = collector.counter.increment("system.usage_total", 10.0)
    await collector.record(org_id, m1)
    await collector.record(org_id, m2)

    # Run Rollup
    rollup = await collector.aggregator.run_rollup(org_id, "system.usage_total", 5)
    assert rollup is not None
    assert rollup.value == 10.0  # Cumulative counters: (5.0 + 15.0) / 2 = 10.0

@pytest.mark.asyncio
async def test_structured_logging():
    repo = InMemoryLogRepository()
    logger = StructuredLogger(repo)
    org_id = "org_1"
    correlation_id = "corr_789"

    log = await logger.log(org_id, correlation_id, "Operation success", level="INFO")
    assert log.id is not None
    assert log.message == "Operation success"
    assert log.context_info["env"] == "production"

    logs = await repo.list_logs(org_id, correlation_id)
    assert len(logs) == 1

@pytest.mark.asyncio
async def test_alert_engine_rules():
    repo = InMemoryAlertRepository()
    engine = AlertEngine(repo)
    
    # Configure policy
    policy = AlertPolicy(
        policy_id="pol_1",
        name="High Latency Alert",
        rules=[
            AlertRule(
                rule_id="rule_1",
                name="SLA Latency Breach",
                condition=AlertCondition(
                    metric_name="system.latency_ms",
                    operator="GREATER_THAN",
                    threshold=500.0
                ),
                severity="CRITICAL"
            )
        ]
    )
    engine.resolver.register_policy(policy)

    # Evaluate healthy metric
    m_healthy = Metric(name="system.latency_ms", value=150.0)
    alerts = await engine.evaluate_metric("org_1", m_healthy)
    assert len(alerts) == 0

    # Evaluate breaching metric
    m_breach = Metric(name="system.latency_ms", value=650.0)
    alerts = await engine.evaluate_metric("org_1", m_breach)
    assert len(alerts) == 1
    assert alerts[0].severity == "CRITICAL"
    assert "SLA Latency Breach" in alerts[0].name

@pytest.mark.asyncio
async def test_event_store_and_timeline_replay():
    replay_repo = InMemoryReplayRepository()
    event_store_repo = InMemoryEventStoreRepository()
    
    event_store = EventStoreService(event_store_repo)
    exe_engine = ExecutionReplayEngine(replay_repo, event_store_repo)

    org_id = "org_1"
    session_id = "session_xyz"

    # Save mock events
    await event_store.record_event("e1", "runtime.execution_started", org_id, session_id, datetime.utcnow(), {"message": "Execution started"})
    await event_store.record_event("e2", "runtime.execution_completed", org_id, session_id, datetime.utcnow() + timedelta(seconds=2), {"message": "Execution finished"})

    # Reconstruct Replay
    replay = await exe_engine.generate_replay(org_id, session_id)
    assert replay is not None
    assert len(replay.timeline_events) == 2
    assert replay.timeline_events[0].module == "runtime"
    assert replay.timeline_events[0].name == "runtime.execution_started"

@pytest.mark.asyncio
@patch("syncsphere.observability.application.services.analytics.PromptExecutionDocument.find")
@patch("syncsphere.observability.application.services.analytics.WorkflowExecutionLogDocument.find")
async def test_analytics_engines(mock_wf_find, mock_prompt_find):
    mock_prompt_query = MagicMock()
    mock_prompt_query.sort.return_value.limit.return_value.to_list = AsyncMock(return_value=[])
    mock_prompt_query.to_list = AsyncMock(return_value=[])
    mock_prompt_find.return_value = mock_prompt_query

    mock_wf_query = MagicMock()
    mock_wf_query.sort.return_value.limit.return_value.to_list = AsyncMock(return_value=[])
    mock_wf_query.to_list = AsyncMock(return_value=[])
    mock_wf_find.return_value = mock_wf_query

    metric_repo = InMemoryMetricRepository()
    event_store_repo = InMemoryEventStoreRepository()
    
    event_store = EventStoreService(event_store_repo)
    ai_engine = AIAnalyticsEngine(metric_repo, event_store_repo)
    conn_engine = ConnectorAnalyticsEngine(metric_repo, event_store_repo)

    org_id = "org_1"
    tgt_user_id = "test_user_id"
    
    # We test the basic empty state mapping since we mocked empty DB results
    ai_stats = await ai_engine.get_ai_analytics(org_id)
    assert ai_stats["token_usage"] == 0

    conn_stats = await conn_engine.get_connector_analytics(org_id, tgt_user_id)
    assert conn_stats["failures"] == 0

@pytest.mark.asyncio
async def test_health_aggregator():
    repo = InMemoryHealthRepository()
    aggregator = HealthAggregator(repo)
    org_id = "org_1"

    check = await aggregator.run_aggregated_checks(org_id)
    assert check is not None
    assert len(check.services) > 0
    assert check.services[0].status == HealthStatus.HEALTHY
