"""
Automation Workflow CRUD API

Provides endpoints to create, list, update, and delete automation workflows
(Zapier-like trigger→actions). Separate from the DAG-based workflow builder.

Also includes:
- POST /v1/automations/{id}/trigger  — manually test-fire a workflow
- GET  /v1/automations/executions    — list execution logs
"""
from datetime import datetime, timezone
from typing import List, Optional

from beanie import PydanticObjectId
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
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
    return AutomationResponse(
        id=str(doc.id),
        name=doc.name,
        is_active=doc.is_active,
        trigger=doc.trigger.model_dump(),
        actions=[a.model_dump() for a in doc.actions],
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
        }

    return {
        "data": [_log_to_dict(l) for l in logs],
        "meta": ResponseMeta(request_id=correlation_id).model_dump(),
    }


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
