import logging
import io
import csv
import json
from typing import List
from fastapi import APIRouter, Request, Depends, status, Query
from fastapi.responses import StreamingResponse
from syncsphere.shared_kernel.infrastructure.http.responses import ResponseEnvelope, ResponseMeta
from syncsphere.shared_kernel.infrastructure.http.dependencies import verify_jwt
from syncsphere.shared_kernel.domain.domain_exception import EntityNotFoundException, ValidationException
from syncsphere.runtime.presentation.schemas import (
    StartExecutionRequest,
    StartExecutionResponse,
    PauseExecutionRequest,
    ResumeExecutionRequest,
    CancelExecutionRequest,
    RetryExecutionRequest,
    ApproveExecutionRequest,
    ExecutionStatusResponse,
    StepStatusResponse,
    ExecutionTimelineResponse,
    TimelineEvent,
    ExecutionMetricsResponse
)
from syncsphere.core.dependency_injection.container import container
from syncsphere.runtime.application.commands import (
    StartExecutionCommand,
    PauseExecutionCommand,
    ResumeExecutionCommand,
    CancelExecutionCommand,
    RetryExecutionCommand,
    ApproveExecutionCommand
)

logger = logging.getLogger("syncsphere.runtime.presentation.routes.runtime_routes")

router = APIRouter(prefix="/runtime", tags=["Runtime"])

def map_session_to_status(session) -> ExecutionStatusResponse:
    steps_map = {}
    for k, v in session.steps.items():
        steps_map[k] = StepStatusResponse(
            node_id=v.node_id,
            name=v.name,
            type=v.type,
            status=v.status.value,
            error=v.error,
            started_at=v.started_at,
            completed_at=v.completed_at,
            retries_attempted=v.retries_attempted
        )
        
    return ExecutionStatusResponse(
        session_id=session.id,
        workflow_id=session.workflow_id,
        version=session.version,
        status=session.status.value,
        variables=session.variables,
        steps=steps_map,
        error_message=session.error_message
    )

@router.post(
    "/start",
    response_model=ResponseEnvelope[StartExecutionResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Spawn and trigger workflow execution session"
)
async def start_execution(
    request: Request,
    body: StartExecutionRequest,
    claims: dict = Depends(verify_jwt)
) -> dict:
    correlation_id = getattr(request.state, "correlation_id", None)
    org_id = claims["org"]

    cmd = StartExecutionCommand(
        org_id=org_id,
        workflow_id=body.workflow_id,
        version=body.version,
        inputs=body.inputs,
        policy=body.policy,
        correlation_id=correlation_id
    )
    
    result = await container.execution_engine.start_execution(cmd)
    if result.is_fail:
        raise result.error()
        
    session = result.value()
    return {
        "data": StartExecutionResponse(
            session_id=session.id,
            status=session.status.value,
            workflow_id=session.workflow_id,
            version=session.version
        ),
        "meta": ResponseMeta(request_id=correlation_id)
    }

@router.post(
    "/pause",
    response_model=ResponseEnvelope[bool],
    summary="Pause active execution session"
)
async def pause_execution(
    request: Request,
    body: PauseExecutionRequest,
    claims: dict = Depends(verify_jwt)
) -> dict:
    correlation_id = getattr(request.state, "correlation_id", None)
    org_id = claims["org"]

    cmd = PauseExecutionCommand(
        org_id=org_id,
        session_id=body.session_id,
        correlation_id=correlation_id
    )
    
    result = await container.execution_engine.pause_execution(cmd)
    if result.is_fail:
        raise result.error()
        
    return {
        "data": result.value(),
        "meta": ResponseMeta(request_id=correlation_id)
    }

@router.post(
    "/resume",
    response_model=ResponseEnvelope[bool],
    summary="Resume a paused execution session"
)
async def resume_execution(
    request: Request,
    body: ResumeExecutionRequest,
    claims: dict = Depends(verify_jwt)
) -> dict:
    correlation_id = getattr(request.state, "correlation_id", None)
    org_id = claims["org"]

    cmd = ResumeExecutionCommand(
        org_id=org_id,
        session_id=body.session_id,
        correlation_id=correlation_id
    )
    
    result = await container.execution_engine.resume_execution(cmd)
    if result.is_fail:
        raise result.error()
        
    return {
        "data": result.value(),
        "meta": ResponseMeta(request_id=correlation_id)
    }

@router.post(
    "/cancel",
    response_model=ResponseEnvelope[bool],
    summary="Abort workflow execution session"
)
async def cancel_execution(
    request: Request,
    body: CancelExecutionRequest,
    claims: dict = Depends(verify_jwt)
) -> dict:
    correlation_id = getattr(request.state, "correlation_id", None)
    org_id = claims["org"]

    cmd = CancelExecutionCommand(
        org_id=org_id,
        session_id=body.session_id,
        correlation_id=correlation_id
    )
    
    result = await container.execution_engine.cancel_execution(cmd)
    if result.is_fail:
        raise result.error()
        
    return {
        "data": result.value(),
        "meta": ResponseMeta(request_id=correlation_id)
    }

@router.post(
    "/retry",
    response_model=ResponseEnvelope[bool],
    summary="Reset failed nodes and retry run"
)
async def retry_execution(
    request: Request,
    body: RetryExecutionRequest,
    claims: dict = Depends(verify_jwt)
) -> dict:
    correlation_id = getattr(request.state, "correlation_id", None)
    org_id = claims["org"]

    cmd = RetryExecutionCommand(
        org_id=org_id,
        session_id=body.session_id,
        correlation_id=correlation_id
    )
    
    result = await container.execution_engine.retry_execution(cmd)
    if result.is_fail:
        raise result.error()
        
    return {
        "data": result.value(),
        "meta": ResponseMeta(request_id=correlation_id)
    }

@router.post(
    "/approve",
    response_model=ResponseEnvelope[bool],
    summary="Submit manual approval gate decision"
)
async def approve_execution(
    request: Request,
    body: ApproveExecutionRequest,
    claims: dict = Depends(verify_jwt)
) -> dict:
    correlation_id = getattr(request.state, "correlation_id", None)
    org_id = claims["org"]

    cmd = ApproveExecutionCommand(
        org_id=org_id,
        session_id=body.session_id,
        node_id=body.node_id,
        approved=body.approved,
        correlation_id=correlation_id
    )
    
    result = await container.execution_engine.approve_execution(cmd)
    if result.is_fail:
        raise result.error()
        
    return {
        "data": result.value(),
        "meta": ResponseMeta(request_id=correlation_id)
    }

@router.get(
    "/status/{session_id}",
    response_model=ResponseEnvelope[ExecutionStatusResponse],
    summary="Retrieve session status details"
)
async def get_status(
    request: Request,
    session_id: str,
    claims: dict = Depends(verify_jwt)
) -> dict:
    correlation_id = getattr(request.state, "correlation_id", None)
    org_id = claims["org"]

    session = await container.execution_session_repo.get_by_id(session_id)
    if not session or session.org_id != org_id:
        raise EntityNotFoundException("EXECUTION_SESSION_NOT_FOUND", "Execution session not found.")
        
    return {
        "data": map_session_to_status(session),
        "meta": ResponseMeta(request_id=correlation_id)
    }

@router.get(
    "/history/{session_id}",
    response_model=ResponseEnvelope[ExecutionTimelineResponse],
    summary="Retrieve execution events timeline history"
)
async def get_history(
    request: Request,
    session_id: str,
    claims: dict = Depends(verify_jwt)
) -> dict:
    correlation_id = getattr(request.state, "correlation_id", None)
    org_id = claims["org"]

    session = await container.execution_session_repo.get_by_id(session_id)
    if not session or session.org_id != org_id:
        raise EntityNotFoundException("EXECUTION_SESSION_NOT_FOUND", "Execution session not found.")
        
    events = [TimelineEvent(**e) for e in session.history.events]
    return {
        "data": ExecutionTimelineResponse(session_id=session.id, events=events),
        "meta": ResponseMeta(request_id=correlation_id)
    }

@router.get(
    "/logs/{session_id}",
    response_model=ResponseEnvelope[List[dict]],
    summary="Retrieve step execution diagnostic logs list"
)
async def get_logs(
    request: Request,
    session_id: str,
    claims: dict = Depends(verify_jwt)
) -> dict:
    correlation_id = getattr(request.state, "correlation_id", None)
    org_id = claims["org"]

    session = await container.execution_session_repo.get_by_id(session_id)
    if not session or session.org_id != org_id:
        raise EntityNotFoundException("EXECUTION_SESSION_NOT_FOUND", "Execution session not found.")
        
    # Return serial step error messages or status audit entries
    logs = []
    for k, v in session.steps.items():
        logs.append({
            "node_id": v.node_id,
            "status": v.status.value,
            "error": v.error,
            "timestamp": v.completed_at.isoformat() if v.completed_at else None
        })
        
    return {
        "data": logs,
        "meta": ResponseMeta(request_id=correlation_id)
    }

@router.get(
    "/timeline/{session_id}",
    response_model=ResponseEnvelope[ExecutionTimelineResponse],
    summary="Retrieve session timeline checkpoints list"
)
async def get_timeline(
    request: Request,
    session_id: str,
    claims: dict = Depends(verify_jwt)
) -> dict:
    return await get_history(request, session_id, claims)

# ─── Export Endpoint ─────────────────────────────────────────────────────────

@router.get(
    "/export/{session_id}",
    summary="Export execution session data as JSON, CSV, or PDF"
)
async def export_execution(
    request: Request,
    session_id: str,
    format: str = Query(default="json", description="json|csv|pdf"),
    claims: dict = Depends(verify_jwt)
):
    org_id = claims["org"]

    session = await container.execution_session_repo.get_by_id(session_id)
    if not session or session.org_id != org_id:
        raise EntityNotFoundException("EXECUTION_SESSION_NOT_FOUND", "Execution session not found.")

    # ─── Build data payload ───────────────────────────────────────────────────
    from datetime import datetime, timezone
    generated_at = datetime.now(timezone.utc).isoformat()
    duration_ms = session.metrics.total_execution_time_ms if session.metrics else 0

    steps_list = []
    for node_id, step in session.steps.items():
        steps_list.append({
            "node_id": step.node_id,
            "name": step.name,
            "type": step.type,
            "status": step.status.value if hasattr(step.status, 'value') else str(step.status),
            "error": step.error,
            "started_at": step.started_at.isoformat() if step.started_at else None,
            "completed_at": step.completed_at.isoformat() if step.completed_at else None,
            "retries_attempted": step.retries_attempted,
        })

    timeline_events = []
    if hasattr(session, 'history') and session.history:
        for ev in session.history.events:
            timeline_events.append(ev if isinstance(ev, dict) else ev.model_dump())

    payload = {
        "workflow_id": session.workflow_id,
        "execution_id": session.id,
        "status": session.status.value if hasattr(session.status, 'value') else str(session.status),
        "version": session.version,
        "started_at": session.metrics.started_at.isoformat() if session.metrics and hasattr(session.metrics, 'started_at') and session.metrics.started_at else None,
        "duration_ms": duration_ms,
        "steps_completed": session.metrics.steps_completed if session.metrics else 0,
        "steps_failed": session.metrics.steps_failed if session.metrics else 0,
        "retry_count": session.metrics.retry_count if session.metrics else 0,
        "error_message": session.error_message,
        "steps": steps_list,
        "timeline": timeline_events,
        "generated_at": generated_at,
    }

    fmt = format.lower()

    # ─── JSON ─────────────────────────────────────────────────────────────────
    if fmt == "json":
        content = json.dumps(payload, indent=2, default=str)
        return StreamingResponse(
            io.BytesIO(content.encode("utf-8")),
            media_type="application/json",
            headers={"Content-Disposition": f'attachment; filename="execution_{session_id[:8]}.json"'},
        )

    # ─── CSV ──────────────────────────────────────────────────────────────────
    elif fmt == "csv":
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=[
            "execution_id", "workflow_id", "overall_status", "version",
            "duration_ms", "node_id", "step_name", "step_type", "step_status",
            "error", "started_at", "completed_at", "retries_attempted", "generated_at"
        ])
        writer.writeheader()
        if steps_list:
            for step in steps_list:
                writer.writerow({
                    "execution_id": payload["execution_id"],
                    "workflow_id": payload["workflow_id"],
                    "overall_status": payload["status"],
                    "version": payload["version"],
                    "duration_ms": payload["duration_ms"],
                    "node_id": step["node_id"],
                    "step_name": step["name"],
                    "step_type": step["type"],
                    "step_status": step["status"],
                    "error": step["error"] or "",
                    "started_at": step["started_at"] or "",
                    "completed_at": step["completed_at"] or "",
                    "retries_attempted": step["retries_attempted"],
                    "generated_at": generated_at,
                })
        else:
            writer.writerow({
                "execution_id": payload["execution_id"],
                "workflow_id": payload["workflow_id"],
                "overall_status": payload["status"],
                "version": payload["version"],
                "duration_ms": payload["duration_ms"],
                "node_id": "", "step_name": "", "step_type": "", "step_status": payload["status"],
                "error": payload["error_message"] or "",
                "started_at": payload["started_at"] or "",
                "completed_at": "",
                "retries_attempted": payload["retry_count"],
                "generated_at": generated_at,
            })
        csv_bytes = output.getvalue().encode("utf-8")
        return StreamingResponse(
            io.BytesIO(csv_bytes),
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="execution_{session_id[:8]}.csv"'},
        )

    # ─── PDF ──────────────────────────────────────────────────────────────────
    elif fmt == "pdf":
        status_color = "#22c55e" if payload["status"] in ("completed", "success") else "#ef4444"
        steps_html = ""
        for s in steps_list:
            sc = "#22c55e" if s["status"] == "success" else ("#ef4444" if s["status"] == "failed" else "#f59e0b")
            err_row = f'<tr><td style="color:#f87171;font-size:11px;padding:4px 12px" colspan="5">{s["error"] or ""}</td></tr>' if s["error"] else ""
            steps_html += f"""
            <tr>
              <td>{s['node_id']}</td>
              <td>{s['name']}</td>
              <td>{s['type']}</td>
              <td style="color:{sc};font-weight:bold">{s['status']}</td>
              <td>{s['retries_attempted']}</td>
            </tr>
            {err_row}"""

        html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<style>
  body {{background:#09090b;color:#e4e4e7;font-family:'Helvetica Neue',Arial,sans-serif;margin:0;padding:32px}}
  h1 {{font-size:26px;font-weight:800;letter-spacing:-1px;margin:0 0 4px}}
  h2 {{font-size:14px;font-weight:700;color:#71717a;text-transform:uppercase;letter-spacing:1px;margin:28px 0 8px}}
  .badge {{display:inline-block;padding:4px 10px;border-radius:6px;font-weight:700;font-size:13px}}
  .grid {{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:8px 0 20px}}
  .stat {{background:#18181b;border:1px solid #3f3f46;border-radius:10px;padding:12px 16px}}
  .stat-label {{font-size:10px;text-transform:uppercase;letter-spacing:1px;color:#71717a;margin-bottom:4px}}
  .stat-value {{font-size:18px;font-weight:700}}
  table {{width:100%;border-collapse:collapse;font-size:12px;margin-top:4px}}
  th {{background:#18181b;padding:8px 12px;text-align:left;border-bottom:1px solid #3f3f46;color:#a1a1aa;text-transform:uppercase;font-size:10px;letter-spacing:1px}}
  td {{padding:8px 12px;border-bottom:1px solid #27272a}}
  .footer {{margin-top:40px;font-size:10px;color:#52525b;text-align:center}}
  .logo {{font-size:18px;font-weight:900;color:#6366f1;letter-spacing:-0.5px}}
</style></head><body>
<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:24px">
  <div>
    <div class="logo">⚡ SyncSphere</div>
    <h1>Execution Report</h1>
    <div style="color:#71717a;font-size:12px">Generated: {generated_at}</div>
  </div>
  <div class="badge" style="background:{status_color}22;color:{status_color};border:1px solid {status_color}55;font-size:18px">
    {'✅' if payload['status'] in ('completed','success') else '❌'} {payload['status'].upper()}
  </div>
</div>

<h2>Execution Summary</h2>
<div class="grid">
  <div class="stat"><div class="stat-label">Execution ID</div><div class="stat-value" style="font-size:11px;font-family:monospace">{payload['execution_id'][:12]}…</div></div>
  <div class="stat"><div class="stat-label">Workflow ID</div><div class="stat-value" style="font-size:11px;font-family:monospace">{payload['workflow_id'][:12]}…</div></div>
  <div class="stat"><div class="stat-label">Duration</div><div class="stat-value">{payload['duration_ms']} ms</div></div>
  <div class="stat"><div class="stat-label">Version</div><div class="stat-value">v{payload['version']}</div></div>
  <div class="stat"><div class="stat-label">Steps OK</div><div class="stat-value" style="color:#22c55e">{payload['steps_completed']}</div></div>
  <div class="stat"><div class="stat-label">Steps Failed</div><div class="stat-value" style="color:#ef4444">{payload['steps_failed']}</div></div>
  <div class="stat"><div class="stat-label">Retries</div><div class="stat-value">{payload['retry_count']}</div></div>
  <div class="stat"><div class="stat-label">Started</div><div class="stat-value" style="font-size:11px">{str(payload['started_at'] or 'N/A')[:19]}</div></div>
</div>

{'<h2>Error</h2><div style="background:#450a0a;border:1px solid #991b1b;border-radius:8px;padding:12px 16px;font-family:monospace;font-size:12px;color:#fca5a5">' + str(payload['error_message']) + '</div>' if payload['error_message'] else ''}

<h2>Step Details</h2>
<table>
<thead><tr><th>Node ID</th><th>Name</th><th>Type</th><th>Status</th><th>Retries</th></tr></thead>
<tbody>{steps_html or '<tr><td colspan="5" style="color:#52525b;text-align:center;padding:16px">No step data recorded</td></tr>'}</tbody>
</table>

<div class="footer">SyncSphere AI Workflow Orchestration Platform — Confidential Execution Report</div>
</body></html>"""

        try:
            import pdfkit  # type: ignore
            pdf_bytes = pdfkit.from_string(html, False, options={"quiet": "", "enable-local-file-access": ""})
        except Exception:
            # Fallback: return the HTML if pdfkit not available
            return StreamingResponse(
                io.BytesIO(html.encode("utf-8")),
                media_type="text/html",
                headers={"Content-Disposition": f'attachment; filename="execution_{session_id[:8]}.html"'},
            )

        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="execution_{session_id[:8]}.pdf"'},
        )

    else:
        raise ValidationException("INVALID_FORMAT", "format must be one of: json, csv, pdf")


@router.get(
    "/metrics/{session_id}",
    response_model=ResponseEnvelope[ExecutionMetricsResponse],
    summary="Retrieve session latency and completion metrics"
)
async def get_metrics(
    request: Request,
    session_id: str,
    claims: dict = Depends(verify_jwt)
) -> dict:
    correlation_id = getattr(request.state, "correlation_id", None)
    org_id = claims["org"]

    session = await container.execution_session_repo.get_by_id(session_id)
    if not session or session.org_id != org_id:
        raise EntityNotFoundException("EXECUTION_SESSION_NOT_FOUND", "Execution session not found.")
        
    return {
        "data": ExecutionMetricsResponse(
            session_id=session.id,
            total_execution_time_ms=session.metrics.total_execution_time_ms,
            steps_completed=session.metrics.steps_completed,
            steps_failed=session.metrics.steps_failed,
            retry_count=session.metrics.retry_count
        ),
        "meta": ResponseMeta(request_id=correlation_id)
    }
