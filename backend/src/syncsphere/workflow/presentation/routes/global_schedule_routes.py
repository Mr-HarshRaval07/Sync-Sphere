import logging
import uuid
from fastapi import APIRouter, Request, Depends, status, HTTPException
from typing import Optional, List
from datetime import datetime, timezone
from pydantic import BaseModel, Field
from beanie import PydanticObjectId

from syncsphere.shared_kernel.infrastructure.http.responses import ResponseEnvelope, ResponseMeta
from syncsphere.shared_kernel.infrastructure.http.dependencies import verify_jwt
from syncsphere.shared_kernel.domain.domain_exception import EntityNotFoundException, ValidationException
from syncsphere.workflow.infrastructure.documents.workflow_schedule_document import WorkflowScheduleDocument
from syncsphere.workflow.infrastructure.documents.workflow_document import WorkflowDocument
from syncsphere.tasks.documents import AutomationWorkflowDocument, WorkflowExecutionLogDocument

logger = logging.getLogger("syncsphere.workflow.presentation.routes.global_schedule_routes")

router = APIRouter(prefix="/v1/schedules", tags=["Global Schedules"])


# ─── Pydantic Request/Response Schemas ───────────────────────────────────────

class CreateScheduleRequest(BaseModel):
    workflow_id: str = Field(..., description="ID of the AutomationWorkflowDocument or WorkflowDocument")
    schedule_type: str = Field(default="once", description="once|hourly|every_x_hours|daily|weekly|monthly|cron")
    cron_expression: Optional[str] = None
    start_date: Optional[str] = Field(default=None, description="ISO 8601 date string e.g. 2026-08-10")
    end_date: Optional[str] = None
    time_of_day: Optional[str] = Field(default=None, description="HH:MM 24hr format")
    timezone: str = Field(default="UTC")
    interval_hours: Optional[int] = None
    day_of_week: Optional[int] = Field(default=None, description="0=Mon..6=Sun")
    day_of_month: Optional[int] = Field(default=None, description="1-31")
    enabled: bool = True

class UpdateScheduleRequest(BaseModel):
    schedule_type: Optional[str] = None
    cron_expression: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    time_of_day: Optional[str] = None
    timezone: Optional[str] = None
    interval_hours: Optional[int] = None
    day_of_week: Optional[int] = None
    day_of_month: Optional[int] = None
    enabled: Optional[bool] = None

class ToggleScheduleRequest(BaseModel):
    enabled: bool

class ScheduleResponse(BaseModel):
    id: str
    workflow_id: str
    workflow_name: Optional[str]
    schedule_type: str
    cron_expression: Optional[str]
    start_date: Optional[str]
    end_date: Optional[str]
    time_of_day: Optional[str]
    timezone: str
    interval_hours: Optional[int]
    day_of_week: Optional[int]
    day_of_month: Optional[int]
    enabled: bool
    status: str
    next_run_at: Optional[str]
    last_run_at: Optional[str]
    run_count: int
    created_at: str

def _compute_next_run(doc: WorkflowScheduleDocument) -> Optional[datetime]:
    """Simple next-run calculator for common schedule types."""
    from datetime import timedelta
    now = datetime.now(timezone.utc)
    try:
        if doc.schedule_type == "once":
            if doc.start_date:
                candidate = datetime.fromisoformat(doc.start_date.replace("Z", "+00:00"))
                return candidate if candidate > now else None
        elif doc.schedule_type == "hourly":
            return now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
        elif doc.schedule_type == "every_x_hours":
            hrs = doc.interval_hours or 1
            return now + timedelta(hours=hrs)
        elif doc.schedule_type in ("daily", "weekly", "monthly"):
            # Return tomorrow at configured time_of_day
            hour, minute = (int(doc.time_of_day.split(":")[0]), int(doc.time_of_day.split(":")[1])) if doc.time_of_day else (9, 0)
            tomorrow = (now + timedelta(days=1)).replace(hour=hour, minute=minute, second=0, microsecond=0)
            return tomorrow
        elif doc.schedule_type == "cron":
            return now + timedelta(hours=1)
    except Exception as e:
        logger.warning(f"Failed to compute next run: {e}")
    return doc.next_run_at

def _doc_to_response(doc: WorkflowScheduleDocument) -> ScheduleResponse:
    # Some older docs might use 'status' natively if they were not migrated, but Pydantic provides defaults
    created_str = doc.created_at.isoformat() if hasattr(doc, "created_at") and doc.created_at else datetime.now(timezone.utc).isoformat()
    return ScheduleResponse(
        id=str(doc.id),
        workflow_id=doc.workflow_id,
        workflow_name=doc.workflow_name,
        schedule_type=doc.schedule_type,
        cron_expression=doc.cron_expression,
        start_date=doc.start_date,
        end_date=doc.end_date,
        time_of_day=doc.time_of_day,
        timezone=doc.timezone,
        interval_hours=doc.interval_hours,
        day_of_week=doc.day_of_week,
        day_of_month=doc.day_of_month,
        enabled=doc.enabled,
        status="active" if doc.enabled else "paused",
        next_run_at=doc.next_run_at.isoformat() if doc.next_run_at else None,
        last_run_at=doc.last_run_at.isoformat() if doc.last_run_at else None,
        run_count=doc.run_count,
        created_at=created_str,
    )

# ─── Endpoints ───────────────────────────────────────────────────────────────

@router.get("", response_model=ResponseEnvelope[List[ScheduleResponse]])
async def list_schedules(request: Request, claims: dict = Depends(verify_jwt)):
    org_id = claims["org"]
    docs = await WorkflowScheduleDocument.find(WorkflowScheduleDocument.org_id == org_id).to_list()
    return ResponseEnvelope(data=[_doc_to_response(d) for d in docs], meta=ResponseMeta(request_id="N/A", status="success"))

@router.get("/{schedule_id}", response_model=ResponseEnvelope[ScheduleResponse])
async def get_schedule(request: Request, schedule_id: str, claims: dict = Depends(verify_jwt)):
    org_id = claims["org"]
    doc = await WorkflowScheduleDocument.find_one(
        WorkflowScheduleDocument.org_id == org_id,
        WorkflowScheduleDocument.id == PydanticObjectId(schedule_id)
    )
    if not doc:
        raise EntityNotFoundException("SCHEDULE_NOT_FOUND", "Schedule not found.")
    return ResponseEnvelope(data=_doc_to_response(doc), meta=ResponseMeta(request_id="N/A", status="success"))

@router.post("", response_model=ResponseEnvelope[ScheduleResponse], status_code=status.HTTP_201_CREATED)
async def create_schedule(request: Request, body: CreateScheduleRequest, claims: dict = Depends(verify_jwt)):
    org_id = claims["org"]
    # Check if workflow exists in DAG Workflows or in Automations
    workflow_name = "Unknown Workflow"
    
    wf_doc = await WorkflowDocument.find_one(WorkflowDocument.org_id == org_id, WorkflowDocument.id == PydanticObjectId(body.workflow_id))
    if wf_doc:
        workflow_name = wf_doc.name
    else:
        auto_doc = await AutomationWorkflowDocument.find_one(AutomationWorkflowDocument.organization_id == org_id, AutomationWorkflowDocument.id == PydanticObjectId(body.workflow_id))
        if auto_doc:
            workflow_name = auto_doc.name or "Automation Task"
        else:
            from syncsphere.tasks.documents import TaskDocument
            task_doc = await TaskDocument.find_one(TaskDocument.organization_id == org_id, TaskDocument.id == PydanticObjectId(body.workflow_id))
            if task_doc:
                workflow_name = task_doc.title or "Standard Task"
            else:
                raise EntityNotFoundException("WORKFLOW_NOT_FOUND", "Workflow ID not found.")

    # Remove old schedules for this workflow to simplify
    old_schedules = await WorkflowScheduleDocument.find(
        WorkflowScheduleDocument.org_id == org_id,
        WorkflowScheduleDocument.workflow_id == body.workflow_id
    ).to_list()
    
    from syncsphere.core.scheduler import scheduler, register_schedule
    for old_sched in old_schedules:
        if scheduler.get_job(str(old_sched.id)):
            scheduler.remove_job(str(old_sched.id))
        await old_sched.delete()

    doc = WorkflowScheduleDocument(
        org_id=org_id,
        workflow_id=body.workflow_id,
        workflow_name=workflow_name,
        schedule_type=body.schedule_type,
        cron_expression=body.cron_expression,
        start_date=body.start_date,
        end_date=body.end_date,
        time_of_day=body.time_of_day,
        timezone=body.timezone,
        interval_hours=body.interval_hours,
        day_of_week=body.day_of_week,
        day_of_month=body.day_of_month,
        enabled=body.enabled,
        created_by=claims.get("sub")
    )
    doc.next_run_at = _compute_next_run(doc)
    await doc.save()
    await register_schedule(doc)
    return ResponseEnvelope(data=_doc_to_response(doc), meta=ResponseMeta(request_id="N/A", status="success"))

@router.put("/{schedule_id}", response_model=ResponseEnvelope[ScheduleResponse])
async def update_schedule(request: Request, schedule_id: str, body: UpdateScheduleRequest, claims: dict = Depends(verify_jwt)):
    org_id = claims["org"]
    doc = await WorkflowScheduleDocument.find_one(
        WorkflowScheduleDocument.org_id == org_id,
        WorkflowScheduleDocument.id == PydanticObjectId(schedule_id)
    )
    if not doc:
        raise EntityNotFoundException("SCHEDULE_NOT_FOUND", "Schedule not found.")

    update_data = body.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(doc, key, value)
    
    doc.next_run_at = _compute_next_run(doc)
    await doc.save()
    
    from syncsphere.core.scheduler import register_schedule
    await register_schedule(doc)
    return ResponseEnvelope(data=_doc_to_response(doc), meta=ResponseMeta(request_id="N/A", status="success"))

@router.patch("/{schedule_id}/toggle", response_model=ResponseEnvelope[ScheduleResponse])
async def toggle_schedule(request: Request, schedule_id: str, body: ToggleScheduleRequest, claims: dict = Depends(verify_jwt)):
    org_id = claims["org"]
    doc = await WorkflowScheduleDocument.find_one(
        WorkflowScheduleDocument.org_id == org_id,
        WorkflowScheduleDocument.id == PydanticObjectId(schedule_id)
    )
    if not doc:
        raise EntityNotFoundException("SCHEDULE_NOT_FOUND", "Schedule not found.")

    doc.enabled = body.enabled
    await doc.save()
    
    from syncsphere.core.scheduler import register_schedule
    await register_schedule(doc)
    return ResponseEnvelope(data=_doc_to_response(doc), meta=ResponseMeta(request_id="N/A", status="success"))

@router.delete("/{schedule_id}")
async def delete_schedule(request: Request, schedule_id: str, claims: dict = Depends(verify_jwt)):
    org_id = claims["org"]
    doc = await WorkflowScheduleDocument.find_one(
        WorkflowScheduleDocument.org_id == org_id,
        WorkflowScheduleDocument.id == PydanticObjectId(schedule_id)
    )
    if not doc:
        raise EntityNotFoundException("SCHEDULE_NOT_FOUND", "Schedule not found.")

    from syncsphere.core.scheduler import scheduler
    if scheduler.get_job(str(doc.id)):
        scheduler.remove_job(str(doc.id))

    await doc.delete()
    return ResponseEnvelope(data={"success": True}, meta=ResponseMeta(request_id="N/A", status="success"))

@router.post("/{schedule_id}/run-now")
async def run_now_schedule(request: Request, schedule_id: str, claims: dict = Depends(verify_jwt)):
    org_id = claims["org"]
    doc = await WorkflowScheduleDocument.find_one(
        WorkflowScheduleDocument.org_id == org_id,
        WorkflowScheduleDocument.id == PydanticObjectId(schedule_id)
    )
    if not doc:
        raise EntityNotFoundException("SCHEDULE_NOT_FOUND", "Schedule not found.")

    doc.last_run_at = datetime.now(timezone.utc)
    doc.run_count += 1
    doc.next_run_at = _compute_next_run(doc)
    await doc.save()

    from syncsphere.core.scheduler import register_schedule, execute_scheduled_job
    await register_schedule(doc)
    
    import asyncio
    asyncio.create_task(execute_scheduled_job(doc.workflow_id, doc.org_id, str(doc.id)))

    return ResponseEnvelope(data=_doc_to_response(doc), meta=ResponseMeta(request_id="N/A", status="success"))
