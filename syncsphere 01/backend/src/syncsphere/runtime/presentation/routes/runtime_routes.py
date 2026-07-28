import logging
from typing import List
from fastapi import APIRouter, Request, Depends, status
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
