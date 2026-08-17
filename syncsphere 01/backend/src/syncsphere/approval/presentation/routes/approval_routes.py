import logging
from fastapi import APIRouter, Request, Depends, status
from typing import List, Optional
from syncsphere.shared_kernel.infrastructure.http.responses import ResponseEnvelope, ResponseMeta
from syncsphere.shared_kernel.infrastructure.http.dependencies import verify_jwt
from syncsphere.shared_kernel.domain.domain_exception import EntityNotFoundException, ValidationException
from syncsphere.approval.presentation.schemas import (
    CreateApprovalRequest,
    SubmitDecisionRequest,
    DelegateRequest,
    AddCommentRequest,
    ApprovalResponse
)
from syncsphere.approval.domain.value_objects import ApprovalHistory, ApprovalStatistics
from syncsphere.approval.application.commands import (
    CreateApprovalCommand,
    ApproveCommand,
    RejectCommand,
    DelegateCommand,
    AddCommentCommand
)
from syncsphere.approval.application.queries import (
    GetApprovalStatusQuery,
    GetApprovalHistoryQuery,
    GetPendingApprovalsQuery,
    GetApprovalStatisticsQuery
)
from syncsphere.core.dependency_injection.container import container

logger = logging.getLogger("syncsphere.approval.presentation.routes.approval_routes")

router = APIRouter(prefix="/approval", tags=["Approval"])

def map_entity_to_response(req) -> ApprovalResponse:
    return ApprovalResponse(
        id=req.id,
        org_id=req.org_id,
        title=req.title,
        description=req.description,
        status=req.status,
        chain=req.chain,
        sla=req.sla,
        escalation_count=req.escalation_count,
        version=req.version,
        created_at=req.created_at,
        completed_at=req.completed_at
    )

@router.post(
    "/request",
    response_model=ResponseEnvelope[ApprovalResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Submit a human approval request"
)
async def create_request(
    request: Request,
    body: CreateApprovalRequest,
    claims: dict = Depends(verify_jwt)
) -> dict:
    correlation_id = getattr(request.state, "correlation_id", None)
    org_id = claims["org"]
    
    cmd = CreateApprovalCommand(
        org_id=org_id,
        title=body.title,
        context=body.context,
        workflow_id=body.workflow_id,
        node_id=body.node_id,
        session_id=body.session_id,
        description=body.description,
        template_id=body.template_id,
        correlation_id=correlation_id
    )
    
    res = await container.approval_service.create_approval(cmd)
    if res.is_fail:
        raise res.error()
        
    return {
        "data": map_entity_to_response(res.value()),
        "meta": ResponseMeta(request_id=correlation_id)
    }

@router.post(
    "/approve",
    response_model=ResponseEnvelope[bool],
    summary="Approve a request at the current stage"
)
async def approve_request(
    request: Request,
    approval_id: str,
    body: SubmitDecisionRequest,
    claims: dict = Depends(verify_jwt)
) -> dict:
    correlation_id = getattr(request.state, "correlation_id", None)
    org_id = claims["org"]
    user_id = claims["sub"]
    
    cmd = ApproveCommand(
        org_id=org_id,
        approval_id=approval_id,
        user_id=user_id,
        comment=body.comment,
        correlation_id=correlation_id
    )
    
    res = await container.approval_service.submit_approval(cmd)
    if res.is_fail:
        raise res.error()
        
    return {
        "data": res.value(),
        "meta": ResponseMeta(request_id=correlation_id)
    }

@router.post(
    "/reject",
    response_model=ResponseEnvelope[bool],
    summary="Reject a request, terminating the chain"
)
async def reject_request(
    request: Request,
    approval_id: str,
    body: SubmitDecisionRequest,
    claims: dict = Depends(verify_jwt)
) -> dict:
    correlation_id = getattr(request.state, "correlation_id", None)
    org_id = claims["org"]
    user_id = claims["sub"]
    
    cmd = RejectCommand(
        org_id=org_id,
        approval_id=approval_id,
        user_id=user_id,
        comment=body.comment,
        correlation_id=correlation_id
    )
    
    res = await container.approval_service.submit_rejection(cmd)
    if res.is_fail:
        raise res.error()
        
    return {
        "data": res.value(),
        "meta": ResponseMeta(request_id=correlation_id)
    }

@router.post(
    "/delegate",
    response_model=ResponseEnvelope[bool],
    summary="Delegate the approval assignment to another user"
)
async def delegate_request(
    request: Request,
    approval_id: str,
    body: DelegateRequest,
    claims: dict = Depends(verify_jwt)
) -> dict:
    correlation_id = getattr(request.state, "correlation_id", None)
    org_id = claims["org"]
    user_id = claims["sub"]
    
    cmd = DelegateCommand(
        org_id=org_id,
        approval_id=approval_id,
        from_user_id=user_id,
        to_user_id=body.to_user_id,
        reason=body.reason,
        correlation_id=correlation_id
    )
    
    res = await container.approval_service.delegate_task(cmd)
    if res.is_fail:
        raise res.error()
        
    return {
        "data": res.value(),
        "meta": ResponseMeta(request_id=correlation_id)
    }

@router.post(
    "/comment",
    response_model=ResponseEnvelope[bool],
    summary="Add a comment to the approval request discussion thread"
)
async def add_comment(
    request: Request,
    approval_id: str,
    body: AddCommentRequest,
    claims: dict = Depends(verify_jwt)
) -> dict:
    correlation_id = getattr(request.state, "correlation_id", None)
    org_id = claims["org"]
    user_id = claims["sub"]
    
    cmd = AddCommentCommand(
        org_id=org_id,
        approval_id=approval_id,
        user_id=user_id,
        text=body.text,
        correlation_id=correlation_id
    )
    
    res = await container.approval_service.add_comment(cmd)
    if res.is_fail:
        raise res.error()
        
    return {
        "data": res.value(),
        "meta": ResponseMeta(request_id=correlation_id)
    }

@router.get(
    "/pending",
    response_model=ResponseEnvelope[List[ApprovalResponse]],
    summary="Retrieve all active approval requests assigned to current user"
)
async def get_pending(
    request: Request,
    claims: dict = Depends(verify_jwt)
) -> dict:
    correlation_id = getattr(request.state, "correlation_id", None)
    org_id = claims["org"]
    user_id = claims["sub"]
    
    query = GetPendingApprovalsQuery(org_id=org_id, user_id=user_id)
    res = await container.approval_service.get_pending_approvals(query)
    if res.is_fail:
        raise res.error()
        
    data = [map_entity_to_response(r) for r in res.value()]
    return {
        "data": data,
        "meta": ResponseMeta(request_id=correlation_id)
    }

@router.get(
    "/history",
    response_model=ResponseEnvelope[List[ApprovalHistory]],
    summary="Retrieve request transition logs"
)
async def get_history(
    request: Request,
    approval_id: str,
    claims: dict = Depends(verify_jwt)
) -> dict:
    correlation_id = getattr(request.state, "correlation_id", None)
    org_id = claims["org"]
    
    query = GetApprovalHistoryQuery(org_id=org_id, approval_id=approval_id)
    res = await container.approval_service.get_approval_history(query)
    if res.is_fail:
        raise res.error()
        
    return {
        "data": res.value(),
        "meta": ResponseMeta(request_id=correlation_id)
    }

@router.get(
    "/statistics",
    response_model=ResponseEnvelope[ApprovalStatistics],
    summary="Retrieve performance SLA metrics and workload bottlenecks"
)
async def get_statistics(
    request: Request,
    workflow_id: Optional[str] = None,
    claims: dict = Depends(verify_jwt)
) -> dict:
    correlation_id = getattr(request.state, "correlation_id", None)
    org_id = claims["org"]
    
    query = GetApprovalStatisticsQuery(org_id=org_id, workflow_id=workflow_id)
    res = await container.approval_service.get_approval_statistics(query)
    if res.is_fail:
        raise res.error()
        
    return {
        "data": res.value(),
        "meta": ResponseMeta(request_id=correlation_id)
    }

@router.get(
    "/audit",
    response_model=ResponseEnvelope[ApprovalResponse],
    summary="Audit approval details with full immutable timeline history"
)
async def get_audit(
    request: Request,
    approval_id: str,
    claims: dict = Depends(verify_jwt)
) -> dict:
    correlation_id = getattr(request.state, "correlation_id", None)
    org_id = claims["org"]
    
    query = GetApprovalStatusQuery(org_id=org_id, approval_id=approval_id)
    res = await container.approval_service.get_approval_status(query)
    if res.is_fail:
        raise res.error()
        
    return {
        "data": map_entity_to_response(res.value()),
        "meta": ResponseMeta(request_id=correlation_id)
    }
