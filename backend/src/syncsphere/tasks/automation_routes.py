"""
Automation Workflow CRUD API

Provides endpoints to create, list, update, and delete automation workflows
(Zapier-like trigger→actions). Separate from the DAG-based workflow builder.

Also includes:
- POST /v1/automations/{id}/trigger          — manually test-fire a workflow
- POST /v1/automations/{id}/duplicate        — clone an automation workflow
- POST /v1/automations/{id}/schedule         — schedule an automation workflow
- GET  /v1/automations/scheduled             — list scheduled automations for org
- GET  /v1/automations/executions            — list execution logs
- GET  /v1/automations/executions/{id}/export — export a single execution log
"""
import io
import csv
import json
from datetime import datetime, timezone
from typing import List, Optional

from beanie import PydanticObjectId
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from syncsphere.shared_kernel.infrastructure.http.dependencies import verify_jwt
from syncsphere.shared_kernel.infrastructure.http.responses import ResponseEnvelope, ResponseMeta
from syncsphere.tasks.documents import (
    AutomationAction,
    AutomationTrigger,
    AutomationWorkflowDocument,
    WorkflowExecutionLogDocument,
)
from syncsphere.workflow.application.action_registry import list_available_actions


router = APIRouter(prefix="/automations", tags=["Automations"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class AutomationActionSchema(BaseModel):
    app: str
    action: str
    config: dict = Field(default_factory=dict)
    requires_approval: bool = False


class AutomationTriggerSchema(BaseModel):
    app: str
    event: str


class CreateAutomationRequest(BaseModel):
    name: str
    trigger: AutomationTriggerSchema
    actions: List[AutomationActionSchema]
    is_active: bool = True


class AutomationResponse(BaseModel):
    id: str
    name: str
    is_active: bool
    trigger: dict
    actions: List[dict]
    created_at: datetime
    updated_at: datetime


def _doc_to_response(doc: AutomationWorkflowDocument) -> AutomationResponse:
    actions_dump = []
    for a in doc.actions:
        dump = a.model_dump()
        dump["requires_approval"] = a.requires_approval
        actions_dump.append(dump)
        
    return AutomationResponse(
        id=str(doc.id),
        name=doc.name,
        is_active=doc.is_active,
        trigger=doc.trigger.model_dump(),
        actions=actions_dump,
        created_at=doc.created_at,
        updated_at=doc.updated_at,
    )


# ---------------------------------------------------------------------------
# GET /v1/automations/actions — List registered actions & capabilities
# ---------------------------------------------------------------------------

@router.get("/actions", tags=["Automations"])
async def list_actions():
    """List all registered actions and their rich capabilities."""
    from syncsphere.workflow.application.action_registry import CAPABILITY_REGISTRY
    return {"capabilities": CAPABILITY_REGISTRY}


# ---------------------------------------------------------------------------
# POST /v1/automations — Create automation workflow
# ---------------------------------------------------------------------------

@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
)
async def create_automation(
    request: Request,
    body: CreateAutomationRequest,
    claims: dict = Depends(verify_jwt),
) -> dict:
    correlation_id = getattr(request.state, "correlation_id", None)
    org_id = claims["org"]
    user_id = claims.get("sub")

    trigger = AutomationTrigger(
        app=body.trigger.app,
        event=body.trigger.event,
    )

    actions = [
        AutomationAction(
            app=a.app,
            action=a.action,
            config=a.config,
            requires_approval=getattr(a, "requires_approval", False)
        )
        for a in body.actions
    ]

    doc = AutomationWorkflowDocument(
        name=body.name,
        user_id=user_id,
        organization_id=org_id,
        is_active=body.is_active,
        trigger=trigger,
        actions=actions,
    )
    await doc.insert()

    return {
        "data": _doc_to_response(doc).model_dump(mode="json"),
        "meta": ResponseMeta(request_id=correlation_id).model_dump(),
    }


# ---------------------------------------------------------------------------
# GET /v1/automations — List automations for org
# ---------------------------------------------------------------------------

@router.get("")
async def list_automations(
    request: Request,
    claims: dict = Depends(verify_jwt),
) -> dict:
    correlation_id = getattr(request.state, "correlation_id", None)
    org_id = claims["org"]

    docs = await AutomationWorkflowDocument.find(
        {"organization_id": org_id}
    ).sort("-created_at").to_list()

    return {
        "data": [_doc_to_response(d).model_dump(mode="json") for d in docs],
        "meta": ResponseMeta(request_id=correlation_id).model_dump(),
    }


# ---------------------------------------------------------------------------
# PATCH /v1/automations/{automation_id}/toggle — Toggle active/inactive
# ---------------------------------------------------------------------------

@router.patch("/{automation_id}/toggle")
async def toggle_automation(
    request: Request,
    automation_id: str,
    claims: dict = Depends(verify_jwt),
) -> dict:
    correlation_id = getattr(request.state, "correlation_id", None)
    org_id = claims["org"]

    try:
        oid = PydanticObjectId(automation_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid automation ID.")

    doc = await AutomationWorkflowDocument.find_one(
        {"_id": oid, "organization_id": org_id}
    )
    if not doc:
        raise HTTPException(status_code=404, detail="Automation not found.")

    doc.is_active = not doc.is_active
    await doc.save()

    return {
        "data": _doc_to_response(doc).model_dump(mode="json"),
        "meta": ResponseMeta(request_id=correlation_id).model_dump(),
    }


# ---------------------------------------------------------------------------
# POST /v1/automations/{automation_id}/trigger — Manually fire workflow
# ---------------------------------------------------------------------------

@router.post("/{automation_id}/trigger")
async def manual_trigger(
    request: Request,
    automation_id: str,
    claims: dict = Depends(verify_jwt),
) -> dict:
    """
    Manually trigger an automation workflow for testing.
    Sends a test payload that matches what the real trigger would send.
    """
    from syncsphere.workflow.application.workflow_executor import execute_workflow

    correlation_id = getattr(request.state, "correlation_id", None)
    org_id = claims["org"]

    try:
        oid = PydanticObjectId(automation_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid automation ID.")

    doc = await AutomationWorkflowDocument.find_one(
        {"_id": oid, "organization_id": org_id}
    )
    if not doc:
        raise HTTPException(status_code=404, detail="Automation not found.")

    # Test trigger data
    test_trigger_data = {
        "task_id": "test-task-id",
        "title": "Test Task from SyncSphere",
        "description": "This is a test trigger from the automation builder.",
        "assigned_to": "Test User",
        "priority": "High",
        "status": "Pending",
        "due_date": "2026-07-30",
        "slack_message": (
            "📌 *Test Trigger*\n\n"
            "*Title:* Test Task from SyncSphere\n"
            "*Assigned To:* Test User\n"
            "*Status:* Pending\n\n"
            "Triggered manually from SyncSphere automation builder 🧪"
        ),
        "email_subject": "Test: New Task from SyncSphere",
        "email_body": (
            "This is a test email triggered manually from SyncSphere.\n\n"
            "Task: Test Task from SyncSphere\n"
            "Priority: High\n"
            "Status: Pending\n"
        ),
    }

    log = await execute_workflow(doc, test_trigger_data)

    return {
        "data": {
            "execution_id": str(log.id),
            "status": log.status,
            "action_results": [r.model_dump(mode="json") for r in log.action_results],
        },
        "meta": ResponseMeta(request_id=correlation_id).model_dump(),
    }


# ---------------------------------------------------------------------------
# GET /v1/automations/executions — List execution logs
# ---------------------------------------------------------------------------

@router.get("/executions")
async def list_executions(
    request: Request,
    workflow_id: Optional[str] = None,
    claims: dict = Depends(verify_jwt),
) -> dict:
    correlation_id = getattr(request.state, "correlation_id", None)
    org_id = claims["org"]

    query: dict = {"organization_id": org_id}
    if workflow_id:
        query["workflow_id"] = workflow_id

    logs = await WorkflowExecutionLogDocument.find(query).sort("-started_at").limit(50).to_list()

    def _log_to_dict(log: WorkflowExecutionLogDocument) -> dict:
        return {
            "id": str(log.id),
            "workflow_id": log.workflow_id,
            "workflow_name": log.workflow_name,
            "status": log.status,
            "action_results": [r.model_dump(mode="json") for r in log.action_results],
            "error": log.error,
            "started_at": log.started_at.isoformat() if log.started_at else None,
            "completed_at": log.completed_at.isoformat() if log.completed_at else None,
            "trigger_type": getattr(log, "trigger_type", "Manual"),
            "schedule_id": getattr(log, "schedule_id", None),
            "environment": getattr(log, "environment", "Production"),
            "trigger_data": log.trigger_data,
            "ai_execution_summary": log.ai_execution_summary,
            "duration_ms": getattr(log, "duration_ms", None),
            "current_step": getattr(log, "current_step", None),
            "user_id": log.user_id,
            "organization_id": log.organization_id,
        }

    return {
        "data": [_log_to_dict(l) for l in logs],
        "meta": ResponseMeta(request_id=correlation_id).model_dump(),
    }


# ---------------------------------------------------------------------------
# POST /v1/automations/{automation_id}/duplicate — Clone an automation workflow
# ---------------------------------------------------------------------------

@router.post("/{automation_id}/duplicate")
async def duplicate_automation(
    request: Request,
    automation_id: str,
    claims: dict = Depends(verify_jwt),
) -> dict:
    """Clone an automation workflow with a 'Copy of …' prefix."""
    correlation_id = getattr(request.state, "correlation_id", None)
    org_id = claims["org"]
    user_id = claims.get("sub")

    try:
        oid = PydanticObjectId(automation_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid automation ID.")

    doc = await AutomationWorkflowDocument.find_one(
        {"_id": oid, "organization_id": org_id}
    )
    if not doc:
        raise HTTPException(status_code=404, detail="Automation not found.")

    new_doc = AutomationWorkflowDocument(
        name=f"Copy of {doc.name}",
        user_id=user_id,
        organization_id=org_id,
        is_active=False,  # start disabled so user can review before activating
        trigger=AutomationTrigger(app=doc.trigger.app, event=doc.trigger.event),
        actions=[
            AutomationAction(
                app=a.app, 
                action=a.action, 
                config=dict(a.config), 
                requires_approval=a.requires_approval
            )
            for a in doc.actions
        ],
    )
    await new_doc.insert()

    return {
        "data": _doc_to_response(new_doc).model_dump(mode="json"),
        "meta": ResponseMeta(request_id=correlation_id).model_dump(),
    }


# ---------------------------------------------------------------------------
# POST /v1/automations/{automation_id}/schedule — Schedule an automation
# ---------------------------------------------------------------------------

class ScheduleAutomationRequest(BaseModel):
    schedule_type: str = Field(..., description="once|hourly|daily|weekly|monthly|every_x_hours")
    start_date: Optional[str] = Field(default=None, description="ISO datetime for one-time run")
    time_of_day: Optional[str] = Field(default=None, description="HH:MM for daily/weekly/monthly")
    interval_hours: Optional[int] = Field(default=None, description="N for every_x_hours")
    enabled: bool = Field(default=True)


@router.post("/{automation_id}/schedule")
async def schedule_automation(
    request: Request,
    automation_id: str,
    body: ScheduleAutomationRequest,
    claims: dict = Depends(verify_jwt),
) -> dict:
    """Create or replace a schedule for an automation workflow."""
    correlation_id = getattr(request.state, "correlation_id", None)
    org_id = claims["org"]

    try:
        oid = PydanticObjectId(automation_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid automation ID.")

    doc = await AutomationWorkflowDocument.find_one(
        {"_id": oid, "organization_id": org_id}
    )
    if not doc:
        raise HTTPException(status_code=404, detail="Automation not found.")

    # Try using the workflow schedule document if available, else store inline
    try:
        from syncsphere.workflow.infrastructure.documents.workflow_schedule_document import WorkflowScheduleDocument


        # Delete any existing schedule for this automation (reuse workflow_id field)
        await WorkflowScheduleDocument.find({"workflow_id": automation_id}).delete()

        next_run: Optional[datetime] = None
        now = datetime.now(timezone.utc)
        try:
            if body.schedule_type == "once" and body.start_date:
                from datetime import datetime as _dt
                next_run = _dt.fromisoformat(body.start_date.replace("Z", "+00:00"))
            elif body.schedule_type == "hourly":
                from datetime import timedelta
                next_run = now + timedelta(hours=1)
            elif body.schedule_type == "every_x_hours" and body.interval_hours:
                from datetime import timedelta
                next_run = now + timedelta(hours=body.interval_hours)
            elif body.schedule_type in ("daily", "weekly", "monthly") and body.time_of_day:
                h, m = (int(x) for x in body.time_of_day.split(":"))
                from datetime import timedelta
                candidate = now.replace(hour=h, minute=m, second=0, microsecond=0)
                if candidate <= now:
                    candidate += timedelta(days=1)
                next_run = candidate
        except Exception:
            pass

        sched_doc = WorkflowScheduleDocument(
            workflow_id=automation_id,
            org_id=org_id,
            schedule_type=body.schedule_type,
            start_date=body.start_date,
            time_of_day=body.time_of_day,
            interval_hours=body.interval_hours,
            enabled=body.enabled,
            next_run=next_run,
        )
        await sched_doc.save()

        return {
            "data": {
                "id": str(sched_doc.id),
                "automation_id": automation_id,
                "automation_name": doc.name,
                "schedule_type": body.schedule_type,
                "enabled": body.enabled,
                "next_run": next_run.isoformat() if next_run else None,
            },
            "meta": ResponseMeta(request_id=correlation_id).model_dump(),
        }
    except ImportError:
        # Fallback: store schedule info as a tag on the automation document
        from beanie.operators import Set
        await doc.update(Set({
            "schedule": {
                "schedule_type": body.schedule_type,
                "start_date": body.start_date,
                "time_of_day": body.time_of_day,
                "interval_hours": body.interval_hours,
                "enabled": body.enabled,
            }
        }))
        return {
            "data": {
                "automation_id": automation_id,
                "automation_name": doc.name,
                "schedule_type": body.schedule_type,
                "enabled": body.enabled,
            },
            "meta": ResponseMeta(request_id=correlation_id).model_dump(),
        }


# ---------------------------------------------------------------------------
# GET /v1/automations/scheduled — List all scheduled automations for org
# ---------------------------------------------------------------------------

@router.get("/scheduled")
async def list_scheduled_automations(
    request: Request,
    claims: dict = Depends(verify_jwt),
) -> dict:
    """List all automation schedules for the current organization."""
    correlation_id = getattr(request.state, "correlation_id", None)
    org_id = claims["org"]

    results = []
    try:
        from syncsphere.workflow.infrastructure.documents.workflow_schedule_document import WorkflowScheduleDocument
        # Fetch all automation schedule docs (automation IDs are stored in workflow_id)
        sched_docs = await WorkflowScheduleDocument.find({"org_id": org_id}).to_list()
        for s in sched_docs:
            # Try to fetch automation name
            name = "Unknown"
            try:
                auto_doc = await AutomationWorkflowDocument.find_one({"_id": PydanticObjectId(s.workflow_id)})
                if auto_doc:
                    name = auto_doc.name
            except Exception:
                pass

            results.append({
                "id": str(s.id),
                "automation_id": s.workflow_id,
                "automation_name": name,
                "schedule_type": s.schedule_type,
                "enabled": s.enabled,
                "next_run": s.next_run.isoformat() if s.next_run else None,
                "created_at": s.created_at.isoformat() if hasattr(s, "created_at") and s.created_at else None,
            })
    except ImportError:
        pass

    return {
        "data": results,
        "meta": ResponseMeta(request_id=correlation_id).model_dump(),
    }


# ---------------------------------------------------------------------------
# GET /v1/automations/executions/{execution_id}/export — Export execution log
# ---------------------------------------------------------------------------

@router.get("/executions/{execution_id}/export", summary="Export execution log as JSON, CSV, or HTML report")
async def export_execution_log(
    request: Request,
    execution_id: str,
    format: str = Query(default="json", description="json|csv|pdf"),
    claims: dict = Depends(verify_jwt),
):
    """Export a WorkflowExecutionLogDocument in JSON, CSV, or PDF (HTML) format."""
    org_id = claims["org"]

    try:
        oid = PydanticObjectId(execution_id)
        log = await WorkflowExecutionLogDocument.find_one(
            {"_id": oid, "organization_id": org_id}
        )
    except Exception:
        log = None

    if not log:
        # Fallback: Treat execution_id as workflow_id (e.g. task_id)
        log = await WorkflowExecutionLogDocument.find_one(
            {"workflow_id": execution_id, "organization_id": org_id},
            sort=[("started_at", -1)]
        )

    if not log:
        raise HTTPException(status_code=404, detail="Execution log not found.")

    generated_at = datetime.now(timezone.utc).isoformat()

    action_results = [
        {
            "action": r.action,
            "status": r.status,
            "error": r.error,
            "started_at": r.started_at.isoformat() if r.started_at else None,
            "completed_at": r.completed_at.isoformat() if r.completed_at else None,
            "attempts": r.attempts,
            "http_metadata": r.http_metadata,
            "resource_links": r.resource_links,
            "input_summary": r.input_summary,
            "output_summary": r.output_summary,
        }
        for r in log.action_results
    ]

    payload = {
        "execution_id": str(log.id),
        "workflow_id": log.workflow_id,
        "workflow_name": log.workflow_name,
        "organization_id": log.organization_id,
        "user_id": log.user_id,
        "status": log.status,
        "trigger_type": getattr(log, "trigger_type", "Manual"),
        "environment": getattr(log, "environment", "Production"),
        "duration_ms": getattr(log, "duration_ms", None),
        "schedule_id": getattr(log, "schedule_id", None),
        "started_at": log.started_at.isoformat() if log.started_at else None,
        "completed_at": log.completed_at.isoformat() if log.completed_at else None,
        "error": log.error,
        "trigger_data": log.trigger_data,
        "ai_execution_summary": log.ai_execution_summary,
        "action_results": action_results,
        "generated_at": generated_at,
    }

    fmt = format.lower()

    if fmt == "json":
        content = json.dumps(payload, indent=2, default=str)
        return StreamingResponse(
            io.BytesIO(content.encode("utf-8")),
            media_type="application/json",
            headers={"Content-Disposition": f'attachment; filename="execution_{execution_id[:8]}.json"'},
        )

    elif fmt == "csv":
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=[
            "execution_id", "workflow_id", "workflow_name", "overall_status",
            "action", "action_status", "error",
            "started_at", "completed_at", "attempts", "generated_at"
        ])
        writer.writeheader()
        if action_results:
            for r in action_results:
                writer.writerow({
                    "execution_id": str(log.id),
                    "workflow_id": log.workflow_id,
                    "workflow_name": log.workflow_name,
                    "overall_status": log.status,
                    "action": r["action"],
                    "action_status": r["status"],
                    "error": r["error"] or "",
                    "started_at": r["started_at"] or "",
                    "completed_at": r["completed_at"] or "",
                    "attempts": r["attempts"],
                    "generated_at": generated_at,
                })
        else:
            writer.writerow({
                "execution_id": str(log.id),
                "workflow_id": log.workflow_id,
                "workflow_name": log.workflow_name,
                "overall_status": log.status,
                "action": "", "action_status": log.status,
                "error": log.error or "",
                "started_at": payload["started_at"] or "",
                "completed_at": payload["completed_at"] or "",
                "attempts": 0,
                "generated_at": generated_at,
            })
        csv_bytes = output.getvalue().encode("utf-8")
        return StreamingResponse(
            io.BytesIO(csv_bytes),
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="execution_{execution_id[:8]}.csv"'},
        )

    elif fmt in ("pdf", "html"):
        status_color = "#22c55e" if log.status in ("success", "completed") else ("#f59e0b" if log.status == "partial" else "#ef4444")
        rows_html = ""
        for r in action_results:
            sc = "#22c55e" if r["status"] == "success" else ("#ef4444" if r["status"] == "failed" else "#f59e0b")
            err_html = f'<tr><td style="color:#f87171;font-size:11px;padding:4px 12px" colspan="5">{r["error"]}</td></tr>' if r["error"] else ""
            rows_html += f"""
            <tr>
              <td>{r['action']}</td>
              <td style="color:{sc};font-weight:bold">{r['status']}</td>
              <td>{r['attempts']}</td>
              <td>{r['started_at'] or 'N/A'}</td>
              <td>{r['completed_at'] or 'N/A'}</td>
            </tr>{err_html}"""

        html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<style>
  body {{background:#09090b;color:#e4e4e7;font-family:'Helvetica Neue',Arial,sans-serif;margin:0;padding:32px}}
  h1 {{font-size:26px;font-weight:800;letter-spacing:-1px;margin:0 0 4px}}
  h2 {{font-size:14px;font-weight:700;color:#71717a;text-transform:uppercase;letter-spacing:1px;margin:28px 0 8px}}
  .badge {{display:inline-block;padding:4px 10px;border-radius:6px;font-weight:700;font-size:13px}}
  .grid {{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin:8px 0 20px}}
  .stat {{background:#18181b;border:1px solid #3f3f46;border-radius:10px;padding:12px 16px}}
  .stat-label {{font-size:10px;text-transform:uppercase;letter-spacing:1px;color:#71717a;margin-bottom:4px}}
  .stat-value {{font-size:16px;font-weight:700}}
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
    {'✅' if log.status in ('success','completed') else ('⚠️' if log.status == 'partial' else '❌')} {log.status.upper()}
  </div>
</div>

<h2>Summary</h2>
<div class="grid">
  <div class="stat"><div class="stat-label">Execution ID</div><div class="stat-value" style="font-size:11px;font-family:monospace">{str(log.id)[:16]}…</div></div>
  <div class="stat"><div class="stat-label">Workflow</div><div class="stat-value" style="font-size:12px">{log.workflow_name}</div></div>
  <div class="stat"><div class="stat-label">Status</div><div class="stat-value" style="color:{status_color}">{log.status}</div></div>
  <div class="stat"><div class="stat-label">Started</div><div class="stat-value" style="font-size:11px">{str(payload['started_at'] or 'N/A')[:19]}</div></div>
  <div class="stat"><div class="stat-label">Completed</div><div class="stat-value" style="font-size:11px">{str(payload['completed_at'] or 'N/A')[:19]}</div></div>
  <div class="stat"><div class="stat-label">Actions</div><div class="stat-value">{len(action_results)}</div></div>
</div>

{'<h2>Error</h2><div style="background:#450a0a;border:1px solid #991b1b;border-radius:8px;padding:12px 16px;font-family:monospace;font-size:12px;color:#fca5a5">' + str(log.error) + '</div>' if log.error else ''}

<h2>Action Details</h2>
<table>
<thead><tr><th>Action</th><th>Status</th><th>Attempts</th><th>Started</th><th>Completed</th></tr></thead>
<tbody>{rows_html or '<tr><td colspan="5" style="color:#52525b;text-align:center;padding:16px">No action data recorded</td></tr>'}</tbody>
</table>

<div class="footer">SyncSphere AI Workflow Orchestration Platform — Confidential Execution Report</div>
</body></html>"""

        try:
            import pdfkit  # type: ignore
            pdf_bytes = pdfkit.from_string(html, False, options={"quiet": "", "enable-local-file-access": ""})
            return StreamingResponse(
                io.BytesIO(pdf_bytes),
                media_type="application/pdf",
                headers={"Content-Disposition": f'attachment; filename="execution_{execution_id[:8]}.pdf"'},
            )
        except Exception:
            return StreamingResponse(
                io.BytesIO(html.encode("utf-8")),
                media_type="text/html",
                headers={"Content-Disposition": f'attachment; filename="execution_{execution_id[:8]}.html"'},
            )
    else:
        raise HTTPException(status_code=400, detail="format must be one of: json, csv, pdf")


# ---------------------------------------------------------------------------
# DELETE /v1/automations/{automation_id}
# ---------------------------------------------------------------------------

@router.delete("/{automation_id}")
async def delete_automation(
    request: Request,
    automation_id: str,
    claims: dict = Depends(verify_jwt),
) -> dict:
    correlation_id = getattr(request.state, "correlation_id", None)
    org_id = claims["org"]

    try:
        oid = PydanticObjectId(automation_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid automation ID.")

    doc = await AutomationWorkflowDocument.find_one(
        {"_id": oid, "organization_id": org_id}
    )
    if not doc:
        raise HTTPException(status_code=404, detail="Automation not found.")

    await doc.delete()

    return {
        "data": True,
        "meta": ResponseMeta(request_id=correlation_id).model_dump(),
    }
