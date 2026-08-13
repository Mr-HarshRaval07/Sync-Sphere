from typing import Dict, Any, List, Optional
from datetime import datetime
from syncsphere.core.events.interfaces import EventPublisher
from syncsphere.observability.domain.entities.alert import Alert
from syncsphere.observability.domain.entities.replay import ExecutionReplay, WorkflowReplay, PlannerReplay
from syncsphere.observability.domain.entities.health import HealthCheck
from syncsphere.observability.domain.value_objects import AlertPolicy, AlertRule, AlertCondition
from syncsphere.observability.domain.repositories import TraceRepository, AlertRepository, LogRepository, HealthRepository, EventStoreRepository
from syncsphere.observability.application.commands import (
    CreateAlertCommand,
    ResolveAlertCommand,
    StartReplayCommand,
    ExportReplayCommand,
    RefreshMetricsCommand
)
from syncsphere.observability.application.queries import (
    TraceDetailsQuery,
    ExecutionTimelineQuery,
    WorkflowTimelineQuery,
    PlannerTimelineQuery,
    MetricsDashboardQuery,
    CostDashboardQuery,
    HealthDashboardQuery,
    AlertDashboardQuery
)
from syncsphere.observability.application.pipelines import (
    TelemetryPipeline,
    LoggingPipeline,
    MetricsPipeline,
    TracingPipeline,
    ReplayPipeline,
    AlertPipeline,
    DashboardPipeline
)
from syncsphere.observability.application.services.live_telemetry import TelemetryBroadcaster
from syncsphere.observability.domain.events import AlertRaised, AlertResolved, ReplayCreated, HealthChanged, MetricCollected

class ObservabilityService:
    """Main application orchestrator driving the Observability bounded context."""
    def __init__(
        self,
        trace_repo: TraceRepository,
        alert_repo: AlertRepository,
        log_repo: LogRepository,
        health_repo: HealthRepository,
        event_store_repo: EventStoreRepository,
        telemetry_pipeline: TelemetryPipeline,
        logging_pipeline: LoggingPipeline,
        metrics_pipeline: MetricsPipeline,
        tracing_pipeline: TracingPipeline,
        replay_pipeline: ReplayPipeline,
        alert_pipeline: AlertPipeline,
        dashboard_pipeline: DashboardPipeline,
        broadcaster: TelemetryBroadcaster,
        event_publisher: Optional[EventPublisher] = None
    ) -> None:
        self.trace_repo = trace_repo
        self.alert_repo = alert_repo
        self.log_repo = log_repo
        self.health_repo = health_repo
        self.event_store_repo = event_store_repo
        self.telemetry_pipeline = telemetry_pipeline
        self.logging_pipeline = logging_pipeline
        self.metrics_pipeline = metrics_pipeline
        self.tracing_pipeline = tracing_pipeline
        self.replay_pipeline = replay_pipeline
        self.alert_pipeline = alert_pipeline
        self.dashboard_pipeline = dashboard_pipeline
        self.broadcaster = broadcaster
        self.event_publisher = event_publisher

    # --- Commands ---
    async def create_alert(self, cmd: CreateAlertCommand) -> Alert:
        alert = Alert(
            org_id=cmd.org_id,
            name=cmd.name,
            message=cmd.message,
            severity=cmd.severity,
            metric_name=cmd.metric_name
        )
        await self.alert_repo.save(alert)
        
        # Publish Event
        if self.event_publisher:
            event = AlertRaised(
                org_id=cmd.org_id,
                correlation_id="N/A",
                alert_id=str(alert.id),
                name=alert.name,
                message=alert.message,
                severity=alert.severity
            )
            await self.event_publisher.publish(event)
        
        # Push Live Broadcast
        await self.broadcaster.alerts.push_alert(
            org_id=cmd.org_id,
            alert_id=str(alert.id),
            alert_name=alert.name,
            message=alert.message,
            severity=alert.severity,
            status=alert.status
        )
        return alert

    async def resolve_alert(self, cmd: ResolveAlertCommand) -> Optional[Alert]:
        alert = await self.alert_repo.get_by_id(cmd.org_id, cmd.alert_id)
        if not alert:
            return None
        
        alert.resolve()
        await self.alert_repo.save(alert)

        # Publish Event
        if self.event_publisher:
            event = AlertResolved(
                org_id=cmd.org_id,
                correlation_id="N/A",
                alert_id=str(alert.id),
                name=alert.name,
                resolved_at=alert.resolved_at
            )
            await self.event_publisher.publish(event)

        # Push Live Broadcast
        await self.broadcaster.alerts.push_alert(
            org_id=cmd.org_id,
            alert_id=str(alert.id),
            alert_name=alert.name,
            message=alert.message,
            severity=alert.severity,
            status=alert.status
        )
        return alert

    async def start_replay(self, cmd: StartReplayCommand) -> Any:
        if cmd.replay_type == "execution":
            replay = await self.replay_pipeline.run_execution_replay(cmd.org_id, cmd.session_id)
        elif cmd.replay_type == "workflow":
            replay = await self.replay_pipeline.run_workflow_replay(cmd.org_id, cmd.session_id)
        elif cmd.replay_type == "planner":
            replay = await self.replay_pipeline.run_planner_replay(cmd.org_id, cmd.session_id)
        else:
            raise ValueError(f"Unknown replay type {cmd.replay_type}")

        # Publish Event
        if self.event_publisher:
            event = ReplayCreated(
                org_id=cmd.org_id,
                correlation_id=cmd.session_id,
                replay_id=str(replay.id),
                session_id=cmd.session_id,
                replay_type=cmd.replay_type
            )
            await self.event_publisher.publish(event)
        
        return replay

    async def export_replay(self, cmd: ExportReplayCommand) -> Any:
        # Resolve replay based on ID
        # Since we're in memory/db, we return a serialized structure
        return {"replay_id": cmd.replay_id, "format": cmd.export_format, "exported_at": datetime.utcnow().isoformat()}

    async def refresh_metrics(self, cmd: RefreshMetricsCommand) -> None:
        # Trigger metric rollups
        await self.telemetry_pipeline.metrics.collector.aggregator.run_rollup(cmd.org_id, "system.usage_total", 5)

    # --- Queries ---
    async def get_trace_details(self, query: TraceDetailsQuery) -> Optional[Dict[str, Any]]:
        trace = await self.trace_repo.get_by_correlation_id(query.org_id, query.trace_id)
        if not trace:
            return None
        
        # Build span list
        spans_list = []
        for s in trace.spans:
            spans_list.append({
                "span_id": s.span_id,
                "name": s.name,
                "parent_span_id": s.parent_span_id,
                "status": s.status,
                "start_time": s.start_time.isoformat(),
                "end_time": s.end_time.isoformat() if s.end_time else None,
                "attributes": s.attributes
            })
            
        return {
            "trace_id": trace.correlation_id,
            "org_id": trace.org_id,
            "spans": spans_list
        }

    async def get_execution_timeline(self, query: ExecutionTimelineQuery) -> List[Dict[str, Any]]:
        replay = await self.replay_pipeline.exe.replay_repo.get_execution_replay(query.org_id, query.session_id)
        if not replay:
            replay = await self.replay_pipeline.run_execution_replay(query.org_id, query.session_id)
        
        return [
            {
                "timestamp": ev.timestamp.isoformat(),
                "name": ev.name,
                "description": ev.description,
                "module": ev.module,
                "context": ev.context_info
            }
            for ev in replay.timeline_events
        ]

    async def get_workflow_timeline(self, query: WorkflowTimelineQuery) -> List[Dict[str, Any]]:
        replay = await self.replay_pipeline.wf.replay_repo.get_workflow_replay(query.org_id, query.workflow_id)
        if not replay:
            replay = await self.replay_pipeline.run_workflow_replay(query.org_id, query.workflow_id)
        return replay.reconstruct_steps

    async def get_planner_timeline(self, query: PlannerTimelineQuery) -> List[Dict[str, Any]]:
        replay = await self.replay_pipeline.pl.replay_repo.get_planner_replay(query.org_id, query.planner_session_id)
        if not replay:
            replay = await self.replay_pipeline.run_planner_replay(query.org_id, query.planner_session_id)
        return replay.reasoning_cycles

    async def get_metrics_dashboard(self, query: MetricsDashboardQuery) -> Dict[str, Any]:
        series = await self.telemetry_pipeline.metrics.collector.repo.get_series(query.org_id, query.metric_name, query.start_time, query.end_time)
        metrics_data = []
        if series:
            for m in series.metrics:
                metrics_data.append({
                    "timestamp": m.timestamp.isoformat(),
                    "value": m.value,
                    "labels": m.labels
                })
        return {
            "metric_name": query.metric_name,
            "org_id": query.org_id,
            "data_points": metrics_data
        }

    async def get_cost_dashboard(self, query: CostDashboardQuery) -> Dict[str, Any]:
        # Aggregate AI costs
        dashboard = await self.dashboard_pipeline.compile_dashboard(query.org_id, query.user_id)
        return dashboard.get("cost", {})

    async def get_health_dashboard(self, query: HealthDashboardQuery) -> Dict[str, Any]:
        dashboard = await self.dashboard_pipeline.compile_dashboard(query.org_id, query.user_id)
        return dashboard.get("health", {})

    async def get_alert_dashboard(self, query: AlertDashboardQuery) -> List[Dict[str, Any]]:
        alerts = await self.alert_repo.list_all(query.org_id)
        if query.status:
            alerts = [a for a in alerts if a.status == query.status]
        return [
            {
                "alert_id": str(a.id),
                "name": a.name,
                "message": a.message,
                "severity": a.severity,
                "status": a.status,
                "metric_name": a.metric_name,
                "created_at": a.created_at.isoformat(),
                "resolved_at": a.resolved_at.isoformat() if a.resolved_at else None
            }
            for a in alerts
        ]
