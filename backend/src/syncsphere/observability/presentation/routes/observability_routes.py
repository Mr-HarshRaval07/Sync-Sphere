import logging
from fastapi import APIRouter, Request, Depends, status, WebSocket, Response
from typing import List, Optional
from datetime import datetime

from syncsphere.shared_kernel.infrastructure.http.responses import ResponseEnvelope, ResponseMeta
from syncsphere.shared_kernel.infrastructure.http.dependencies import get_org_id, verify_jwt

from syncsphere.observability.presentation.schemas import (
    AlertCreateRequest,
    ReplayStartRequest,
    AlertResponse,
    ReplayResponse,
    TraceResponse,
    TraceSpanResponse
)
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
from syncsphere.core.dependency_injection.container import container
from syncsphere.observability.infrastructure.exporters import PrometheusExporter

logger = logging.getLogger("syncsphere.observability.presentation.routes")

router = APIRouter(prefix="/observability", tags=["Observability"])

@router.get("/traces", response_model=ResponseEnvelope)
async def list_traces(org_id: str = Depends(get_org_id), limit: int = 100):
    traces = await container.observability_service.trace_repo.list_by_org(org_id, limit)
    data = []
    for t in traces:
        data.append({
            "trace_id": t.correlation_id,
            "org_id": t.org_id,
            "span_count": len(t.spans)
        })
    return ResponseEnvelope(
        data=data,
        meta=ResponseMeta(request_id="N/A", status="success")
    )

@router.get("/traces/{id}", response_model=ResponseEnvelope)
async def get_trace(id: str, org_id: str = Depends(get_org_id)):
    query = TraceDetailsQuery(org_id=org_id, trace_id=id)
    details = await container.observability_service.get_trace_details(query)
    if not details:
        return ResponseEnvelope(
            data=None,
            meta=ResponseMeta(request_id="N/A", status="error")
        )
    return ResponseEnvelope(
        data=details,
        meta=ResponseMeta(request_id="N/A", status="success")
    )

@router.get("/replay/{id}", response_model=ResponseEnvelope)
async def get_replay(id: str, type: str = "execution", org_id: str = Depends(get_org_id)):
    if type == "execution":
        query = ExecutionTimelineQuery(org_id=org_id, session_id=id)
        events = await container.observability_service.get_execution_timeline(query)
    elif type == "workflow":
        query = WorkflowTimelineQuery(org_id=org_id, workflow_id=id)
        events = await container.observability_service.get_workflow_timeline(query)
    elif type == "planner":
        query = PlannerTimelineQuery(org_id=org_id, planner_session_id=id)
        events = await container.observability_service.get_planner_timeline(query)
    else:
        return ResponseEnvelope(
            data=None,
            meta=ResponseMeta(request_id="N/A", status="error")
        )
    return ResponseEnvelope(
        data={"replay_type": type, "session_id": id, "timeline_events": events},
        meta=ResponseMeta(request_id="N/A", status="success")
    )

@router.post("/replay", response_model=ResponseEnvelope)
async def start_replay(body: ReplayStartRequest, org_id: str = Depends(get_org_id)):
    cmd = StartReplayCommand(org_id=org_id, session_id=body.session_id, replay_type=body.replay_type)
    replay = await container.observability_service.start_replay(cmd)
    return ResponseEnvelope(
        data={"replay_id": str(replay.id), "session_id": replay.session_id, "replay_type": body.replay_type},
        meta=ResponseMeta(request_id="N/A", status="success")
    )

@router.get("/metrics", response_model=ResponseEnvelope)
async def get_metrics(metric_name: str, start_time: Optional[str] = None, end_time: Optional[str] = None, org_id: str = Depends(get_org_id)):
    st = datetime.fromisoformat(start_time) if start_time else None
    et = datetime.fromisoformat(end_time) if end_time else None
    query = MetricsDashboardQuery(org_id=org_id, metric_name=metric_name, start_time=st, end_time=et)
    dashboard = await container.observability_service.get_metrics_dashboard(query)
    return ResponseEnvelope(
        data=dashboard,
        meta=ResponseMeta(request_id="N/A", status="success")
    )

@router.get("/metrics/prometheus")
async def get_prometheus_metrics(org_id: str = Depends(get_org_id)):
    # Scan all metrics for this organization
    metric_names = await container.observability_service.telemetry_pipeline.metrics.collector.repo.list_metric_names(org_id)
    series_list = []
    for name in metric_names:
        series = await container.observability_service.telemetry_pipeline.metrics.collector.repo.get_series(org_id, name)
        if series:
            series_list.append(series)
    
    exporter = PrometheusExporter()
    text_data = exporter.format_to_text(series_list)
    return Response(content=text_data, media_type="text/plain")

@router.get("/dashboard", response_model=ResponseEnvelope[dict])
async def get_dashboard(org_id: str = Depends(get_org_id), claims: dict = Depends(verify_jwt)):
    user_id = claims["sub"]
    data = await container.observability_service.dashboard_pipeline.compile_dashboard(org_id, user_id)
    return ResponseEnvelope(
        data=data,
        meta=ResponseMeta(request_id="N/A", status="success")
    )

@router.get("/dashboard/metrics", response_model=ResponseEnvelope[dict])
async def get_dashboard_metrics_legacy(org_id: str = Depends(get_org_id), claims: dict = Depends(verify_jwt)):
    user_id = claims["sub"]
    data = await container.observability_service.dashboard_pipeline.compile_dashboard(org_id, user_id)
    return ResponseEnvelope(data=data, meta=ResponseMeta(request_id="N/A", status="success"))

@router.get("/analytics", response_model=ResponseEnvelope[dict])
async def get_analytics_legacy(org_id: str = Depends(get_org_id), claims: dict = Depends(verify_jwt)):
    user_id = claims["sub"]
    data = await container.observability_service.dashboard_pipeline.compile_dashboard(org_id, user_id)
    return ResponseEnvelope(data=data, meta=ResponseMeta(request_id="N/A", status="success"))

@router.get("/ai/usage", response_model=ResponseEnvelope[dict])
async def get_ai_usage_legacy(org_id: str = Depends(get_org_id)):
    data = await container.observability_service.dashboard_pipeline.ai.get_ai_analytics(org_id)
    return ResponseEnvelope(data=data, meta=ResponseMeta(request_id="N/A", status="success"))

@router.get("/ai/executions/raw")
async def get_raw_ai_executions(org_id: str = Depends(get_org_id)):
    from syncsphere.ai.infrastructure.documents.execution_document import PromptExecutionDocument
    docs = await PromptExecutionDocument.find({"org_id": org_id}).to_list()
    data = []
    for d in docs:
        data.append({
            "created_at": d.created_at.isoformat() if d.created_at else None,
            "prompt_tokens": d.prompt_tokens or 0,
            "completion_tokens": d.completion_tokens or 0,
            "total_tokens": d.total_tokens or 0
        })
    return ResponseEnvelope(data=data, meta=ResponseMeta(request_id="N/A", status="success"))

@router.get("/health", response_model=ResponseEnvelope)
async def get_health(org_id: str = Depends(get_org_id), claims: dict = Depends(verify_jwt)):
    user_id = claims["sub"]
    query = HealthDashboardQuery(org_id=org_id, user_id=user_id)
    report = await container.observability_service.get_health_dashboard(query)
    return ResponseEnvelope(
        data=report,
        meta=ResponseMeta(request_id="N/A", status="success")
    )

@router.get("/alerts", response_model=ResponseEnvelope)
async def get_alerts(status: Optional[str] = None, org_id: str = Depends(get_org_id)):
    query = AlertDashboardQuery(org_id=org_id, status=status)
    alerts = await container.observability_service.get_alert_dashboard(query)
    return ResponseEnvelope(
        data=alerts,
        meta=ResponseMeta(request_id="N/A", status="success")
    )

@router.post("/alerts", response_model=ResponseEnvelope)
async def create_alert(body: AlertCreateRequest, org_id: str = Depends(get_org_id)):
    cmd = CreateAlertCommand(
        org_id=org_id,
        name=body.name,
        message=body.message,
        severity=body.severity,
        metric_name=body.metric_name
    )
    alert = await container.observability_service.create_alert(cmd)
    return ResponseEnvelope(
        data={"alert_id": str(alert.id), "status": alert.status},
        meta=ResponseMeta(request_id="N/A", status="success")
    )

@router.patch("/alerts/{id}/resolve", response_model=ResponseEnvelope)
async def resolve_alert(id: str, request: Request, org_id: str = Depends(get_org_id)):
    body = await request.json()
    status_val = body.get("status", "RESOLVED")
    cmd = ResolveAlertCommand(org_id=org_id, alert_id=id, status=status_val)
    alert = await container.observability_service.resolve_alert(cmd)
    return ResponseEnvelope(
        data={"alert_id": str(alert.id), "status": alert.status},
        meta=ResponseMeta(request_id="N/A", status="success")
    )

@router.websocket("/live")
async def live_websocket(websocket: WebSocket, org_id: str):
    await container.observability_websocket_hub.connect(org_id, websocket)
    try:
        while True:
            # Wait for any message from client
            await websocket.receive_text()
    except Exception:
        pass
    finally:
        container.observability_websocket_hub.disconnect(org_id, websocket)
