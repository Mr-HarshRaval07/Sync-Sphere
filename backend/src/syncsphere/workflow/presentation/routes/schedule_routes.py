import logging
from fastapi import APIRouter, Request, Depends, status, HTTPException
from typing import Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field
from syncsphere.shared_kernel.infrastructure.http.responses import ResponseEnvelope, ResponseMeta
from syncsphere.shared_kernel.infrastructure.http.dependencies import verify_jwt
from syncsphere.shared_kernel.domain.domain_exception import EntityNotFoundException, ValidationException
from syncsphere.workflow.infrastructure.documents.workflow_schedule_document import WorkflowScheduleDocument
from syncsphere.workflow.infrastructure.documents.workflow_document import WorkflowDocument

logger = logging.getLogger("syncsphere.workflow.presentation.routes.schedule_routes")

router = APIRouter(prefix="/workflows", tags=["Workflow Schedules"])


# ─── Pydantic Request/Response Schemas ───────────────────────────────────────

class CreateScheduleRequest(BaseModel):
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


class UpdateScheduleStatusRequest(BaseModel):
    status: str = Field(..., description="enabled|paused|disabled")


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
    status: str
    next_run_at: Optional[str]
    last_run_at: Optional[str]
    run_count: int
    created_at: str


# ─── Helpers ─────────────────────────────────────────────────────────────────

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
            # Return a placeholder — real cron parsing requires croniter
            return now + timedelta(hours=1)
    except Exception:
        pass
    return None


def _doc_to_response(doc: WorkflowScheduleDocument) -> ScheduleResponse:
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
        status=doc.status,
        next_run_at=doc.next_run_at.isoformat() if doc.next_run_at else None,
        last_run_at=doc.last_run_at.isoformat() if doc.last_run_at else None,
        run_count=doc.run_count,
        created_at=doc.created_at.isoformat() if hasattr(doc, "created_at") and doc.created_at else datetime.now(timezone.utc).isoformat(),
    )


# ─── Endpoints ───────────────────────────────────────────────────────────────

@router.post(
    "/{workflow_id}/schedule",
    response_model=ResponseEnvelope[ScheduleResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create or replace a workflow schedule"
)
async def create_schedule(
    request: Request,
    workflow_id: str,
    body: CreateScheduleRequest,
    claims: dict = Depends(verify_jwt)
) -> dict:
    correlation_id = getattr(request.state, "correlation_id", None)
    org_id = claims["org"]
    user_id = claims.get("sub", None)

    # Validate workflow exists in org
    wf_doc = await WorkflowDocument.find_one(
        WorkflowDocument.org_id == org_id,
        WorkflowDocument.id == workflow_id  # type: ignore[arg-type]
    )
    if not wf_doc:
        # Try by str id
        from beanie import PydanticObjectId
        try:
            wf_doc = await WorkflowDocument.find_one(
                WorkflowDocument.org_id == org_id,
                WorkflowDocument.id == PydanticObjectId(workflow_id)  # type: ignore[arg-type]
            )
        except Exception:
            pass
    if not wf_doc:
        raise EntityNotFoundException("WORKFLOW_NOT_FOUND", "Workflow not found.")

    # Validate: prevent past start_date for "once" type
    if body.schedule_type == "once" and body.start_date:
        try:
            dt = datetime.fromisoformat(body.start_date.replace("Z", "+00:00"))
            if dt <= datetime.now(timezone.utc):
                raise ValidationException("PAST_SCHEDULE_DATE", "Start date must be in the future.")
        except ValidationException:
            raise
        except Exception:
            raise ValidationException("INVALID_DATE", "Invalid start_date format. Use ISO 8601.")

    # Validate cron expression for cron type
    if body.schedule_type == "cron" and not body.cron_expression:
        raise ValidationException("MISSING_CRON", "cron_expression is required for 'cron' schedule type.")

    # Delete existing schedules for this workflow (replace behaviour)
    await WorkflowScheduleDocument.find(
        WorkflowScheduleDocument.org_id == org_id,
        WorkflowScheduleDocument.workflow_id == workflow_id,
    ).delete()

    doc = WorkflowScheduleDocument(
        org_id=org_id,
        workflow_id=workflow_id,
        workflow_name=wf_doc.name,
        schedule_type=body.schedule_type,
        cron_expression=body.cron_expression,
        start_date=body.start_date,
        end_date=body.end_date,
        time_of_day=body.time_of_day,
        timezone=body.timezone,
        interval_hours=body.interval_hours,
        day_of_week=body.day_of_week,
        day_of_month=body.day_of_month,
        status="enabled" if body.enabled else "disabled",
        created_by=user_id,
    )
    doc.next_run_at = _compute_next_run(doc)
    await doc.save()

    logger.info("Schedule created for workflow %s in org %s", workflow_id, org_id)
    return {
        "data": _doc_to_response(doc),
        "meta": ResponseMeta(request_id=correlation_id)
    }


@router.get(
    "/{workflow_id}/schedule",
    response_model=ResponseEnvelope[ScheduleResponse],
    summary="Get the active schedule for a workflow"
)
async def get_schedule(
    request: Request,
    workflow_id: str,
    claims: dict = Depends(verify_jwt)
) -> dict:
    correlation_id = getattr(request.state, "correlation_id", None)
    org_id = claims["org"]

    doc = await WorkflowScheduleDocument.find_one(
        WorkflowScheduleDocument.org_id == org_id,
        WorkflowScheduleDocument.workflow_id == workflow_id,
    )
    if not doc:
        raise EntityNotFoundException("SCHEDULE_NOT_FOUND", "No schedule found for this workflow.")

    return {
        "data": _doc_to_response(doc),
        "meta": ResponseMeta(request_id=correlation_id)
    }


@router.patch(
    "/{workflow_id}/schedule/status",
    response_model=ResponseEnvelope[ScheduleResponse],
    summary="Enable, pause, or disable a workflow schedule"
)
async def update_schedule_status(
    request: Request,
    workflow_id: str,
    body: UpdateScheduleStatusRequest,
    claims: dict = Depends(verify_jwt)
) -> dict:
    correlation_id = getattr(request.state, "correlation_id", None)
    org_id = claims["org"]

    if body.status not in ("enabled", "paused", "disabled"):
        raise ValidationException("INVALID_STATUS", "Status must be one of: enabled, paused, disabled")

    doc = await WorkflowScheduleDocument.find_one(
        WorkflowScheduleDocument.org_id == org_id,
        WorkflowScheduleDocument.workflow_id == workflow_id,
    )
    if not doc:
        raise EntityNotFoundException("SCHEDULE_NOT_FOUND", "No schedule found for this workflow.")

    doc.status = body.status
    if body.status == "enabled":
        doc.next_run_at = _compute_next_run(doc)
    elif body.status in ("paused", "disabled"):
        doc.next_run_at = None
    await doc.save()

    return {
        "data": _doc_to_response(doc),
        "meta": ResponseMeta(request_id=correlation_id)
    }


@router.delete(
    "/{workflow_id}/schedule",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a workflow schedule"
)
async def delete_schedule(
    workflow_id: str,
    claims: dict = Depends(verify_jwt)
) -> None:
    org_id = claims["org"]
    await WorkflowScheduleDocument.find(
        WorkflowScheduleDocument.org_id == org_id,
        WorkflowScheduleDocument.workflow_id == workflow_id,
    ).delete()
