from typing import Dict, Any, List, Optional
from datetime import datetime
from syncsphere.observability.domain.entities.trace import TraceSpan
from syncsphere.observability.domain.entities.alert import Alert
from syncsphere.observability.domain.entities.replay import ExecutionReplay, WorkflowReplay, PlannerReplay
from syncsphere.observability.domain.entities.health import HealthCheck
from syncsphere.observability.domain.value_objects import Metric, HealthStatus
from syncsphere.observability.application.services.tracing import DistributedTracer, TraceCollector
from syncsphere.observability.application.services.metrics import MetricsCollector
from syncsphere.observability.application.services.logging import StructuredLogger
from syncsphere.observability.application.services.replay import ExecutionReplayEngine, WorkflowReplayEngine, PlannerReplayEngine
from syncsphere.observability.application.services.alerting import AlertEngine
from syncsphere.observability.application.services.health import HealthAggregator
from syncsphere.observability.application.services.analytics import (
    AIAnalyticsEngine,
    ConnectorAnalyticsEngine,
    PlannerAnalytics,
    RuntimeAnalytics,
    KnowledgeAnalytics,
    ApprovalAnalytics,
    OrganizationAnalytics,
    UsageAnalytics,
    CostAnalytics
)
from syncsphere.observability.application.services.event_store_service import EventStoreService

class LoggingPipeline:
    def __init__(self, logger: StructuredLogger) -> None:
        self.logger = logger

    async def process_log(self, org_id: str, correlation_id: str, message: str, level: str, module: str, context: Optional[Dict[str, Any]] = None) -> Any:
        return await self.logger.log(org_id, correlation_id, message, level, module, context)

class MetricsPipeline:
    def __init__(self, collector: MetricsCollector) -> None:
        self.collector = collector

    async def process_metric(self, org_id: str, metric_name: str, value: float, labels: Optional[Dict[str, str]] = None) -> Metric:
        metric = Metric(name=metric_name, value=value, labels=labels or {}, timestamp=datetime.utcnow())
        await self.collector.record(org_id, metric)
        return metric

class TracingPipeline:
    def __init__(self, collector: TraceCollector) -> None:
        self.collector = collector

    async def process_event_trace(self, event_type: str, org_id: str, correlation_id: str, payload: Dict[str, Any]) -> None:
        await self.collector.collect_from_event(event_type, org_id, correlation_id, payload)

class ReplayPipeline:
    def __init__(self, exe: ExecutionReplayEngine, wf: WorkflowReplayEngine, pl: PlannerReplayEngine) -> None:
        self.exe = exe
        self.wf = wf
        self.pl = pl

    async def run_execution_replay(self, org_id: str, session_id: str) -> ExecutionReplay:
        return await self.exe.generate_replay(org_id, session_id)

    async def run_workflow_replay(self, org_id: str, workflow_id: str) -> WorkflowReplay:
        return await self.wf.generate_replay(org_id, workflow_id)

    async def run_planner_replay(self, org_id: str, planner_session_id: str) -> PlannerReplay:
        return await self.pl.generate_replay(org_id, planner_session_id)

class AlertPipeline:
    def __init__(self, engine: AlertEngine) -> None:
        self.engine = engine

    async def evaluate_and_raise(self, org_id: str, metric: Metric) -> List[Alert]:
        return await self.engine.evaluate_metric(org_id, metric)

class DashboardPipeline:
    def __init__(
        self,
        ai: AIAnalyticsEngine,
        conn: ConnectorAnalyticsEngine,
        plan: PlannerAnalytics,
        run: RuntimeAnalytics,
        know: KnowledgeAnalytics,
        appr: ApprovalAnalytics,
        org: OrganizationAnalytics,
        use: UsageAnalytics,
        cost: CostAnalytics,
        health: HealthAggregator
    ) -> None:
        self.ai = ai
        self.conn = conn
        self.plan = plan
        self.run = run
        self.know = know
        self.appr = appr
        self.org = org
        self.use = use
        self.cost = cost
        self.health = health

    async def compile_dashboard(self, org_id: str, user_id: str) -> Dict[str, Any]:
        ai_data = await self.ai.get_ai_analytics(org_id)
        conn_data = await self.conn.get_connector_analytics(org_id, user_id)
        plan_data = await self.plan.get_planner_stats(org_id, user_id)
        run_data = await self.run.get_runtime_stats(org_id, user_id)
        know_data = await self.know.get_knowledge_stats(org_id, user_id)
        appr_data = await self.appr.get_approval_stats(org_id, user_id)
        org_data = await self.org.get_org_stats(org_id, user_id)
        use_data = await self.use.get_usage_stats(org_id, user_id)
        cost_data = await self.cost.get_cost_stats(org_id, user_id)
        health_status = await self.health.run_aggregated_checks(org_id)

        # Convert health check to dict format
        health_report = {
            "overall_status": HealthStatus.HEALTHY.value,
            "services": [{"name": s.name, "status": s.status.value, "message": s.message} for s in health_status.services]
        }
        for s in health_status.services:
            if s.status == HealthStatus.UNHEALTHY:
                health_report["overall_status"] = HealthStatus.UNHEALTHY.value
                break
            elif s.status == HealthStatus.DEGRADED and health_report["overall_status"] != HealthStatus.UNHEALTHY.value:
                health_report["overall_status"] = HealthStatus.DEGRADED.value

        return {
            "organization": org_data,
            "health": health_report,
            "ai_gateway": ai_data,
            "connectors": conn_data,
            "planner": plan_data,
            "executions": run_data,
            "knowledge": know_data,
            "approval": appr_data,
            "usage": use_data,
            "cost": cost_data,
            "timestamp": datetime.utcnow().isoformat()
        }


class TelemetryPipeline:
    """Unified entry pipeline parsing raw telemetry and routing across engines."""
    def __init__(
        self,
        logging: LoggingPipeline,
        metrics: MetricsPipeline,
        tracing: TracingPipeline,
        alerts: AlertPipeline,
        event_store: EventStoreService
    ) -> None:
        self.logging = logging
        self.metrics = metrics
        self.tracing = tracing
        self.alerts = alerts
        self.event_store = event_store

    async def ingest_telemetry_event(self, event_id: str, event_type: str, org_id: str, correlation_id: str, timestamp: datetime, payload: Dict[str, Any]) -> None:
        # 1. Record event into EventStore
        await self.event_store.record_event(
            event_id=event_id,
            event_type=event_type,
            org_id=org_id,
            correlation_id=correlation_id,
            timestamp=timestamp,
            payload=payload
        )

        # 2. Extract and log structured log entry
        message = payload.get("message") or f"Telemetry event: {event_type} occurred."
        level = "ERROR" if "failed" in event_type.lower() or "error" in event_type.lower() else "INFO"
        module = event_type.split(".")[0] if "." in event_type else "system"
        await self.logging.process_log(org_id, correlation_id, message, level, module, payload)

        # 3. Handle tracing spans asynchronously
        await self.tracing.process_event_trace(event_type, org_id, correlation_id, payload)

        # 4. Handle metric updates from events
        if "latency" in payload or "duration_ms" in payload:
            duration = payload.get("latency") or payload.get("duration_ms") or 0.0
            metric = await self.metrics.process_metric(org_id, f"{module}.latency_ms", float(duration), {"event": event_type})
            await self.alerts.evaluate_and_raise(org_id, metric)

        if "tokens" in payload:
            total_tokens = payload.get("tokens", {}).get("total_tokens", 0)
            metric = await self.metrics.process_metric(org_id, "ai.tokens_total", float(total_tokens))
            await self.alerts.evaluate_and_raise(org_id, metric)

        if "cost" in payload:
            cost = payload.get("cost", 0.0)
            metric = await self.metrics.process_metric(org_id, "ai.cost_dollars_total", float(cost))
            await self.alerts.evaluate_and_raise(org_id, metric)

        if "fail" in event_type.lower() or "error" in event_type.lower():
            metric = await self.metrics.process_metric(org_id, f"{module}.errors_total", 1.0)
            await self.alerts.evaluate_and_raise(org_id, metric)

        # Keep incrementing global usage metric
        metric = await self.metrics.process_metric(org_id, f"{module}.usage_total", 1.0)
        await self.alerts.evaluate_and_raise(org_id, metric)
