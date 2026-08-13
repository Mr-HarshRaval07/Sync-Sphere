from fastapi import APIRouter, Depends, Request, status, HTTPException
from syncsphere.shared_kernel.infrastructure.http.responses import ResponseEnvelope, ResponseMeta
from syncsphere.shared_kernel.infrastructure.http.dependencies import verify_jwt
from syncsphere.planner.presentation.schemas import (
    WorkflowGenerateRequest,
    WorkflowImproveRequest,
    WorkflowExplainRequest,
    WorkflowValidateRequest
)
from syncsphere.planner.application.commands import (
    GenerateWorkflowCommand,
    ImproveWorkflowCommand,
    ExplainWorkflowCommand,
    ValidateWorkflowPromptCommand
)
from syncsphere.planner.application.queries import (
    PreviewWorkflowQuery,
    PreviewExecutionGraphQuery,
    ExplainPlanQuery,
    EstimateExecutionCostQuery,
    EstimateExecutionTimeQuery
)

router = APIRouter(prefix="/planner", tags=["Agentic Planner"])

@router.post(
    "/generate",
    response_model=ResponseEnvelope[dict],
    status_code=status.HTTP_201_CREATED,
    summary="Generate a workflow plan aggregate from user prompt"
)
async def generate_workflow(
    request: Request,
    body: WorkflowGenerateRequest,
    claims: dict = Depends(verify_jwt)
) -> dict:
    from syncsphere.core.dependency_injection.container import container
    correlation_id = getattr(request.state, "correlation_id", None)
    org_id = claims["org"]
    user_id = claims["sub"]
    
    cmd = GenerateWorkflowCommand(
        org_id=org_id,
        user_id=user_id,
        prompt=body.prompt,
        strategy=body.strategy
    )
    
    res = await container.planner_service.generate_workflow(cmd)
    if res.is_fail:
        raise HTTPException(status_code=422, detail=str(res.error()))
        
    wf = res.value()
    return {
        "data": {
            "workflow_id": wf.id,
            "name": wf.name,
            "status": wf.status.value,
            "nodes_count": len(wf.graph.nodes)
        },
        "meta": ResponseMeta(request_id=correlation_id)
    }

@router.post(
    "/improve",
    response_model=ResponseEnvelope[dict],
    summary="Refine the workflow graph based on natural language feedback"
)
async def improve_workflow(
    request: Request,
    body: WorkflowImproveRequest,
    claims: dict = Depends(verify_jwt)
) -> dict:
    from syncsphere.core.dependency_injection.container import container
    correlation_id = getattr(request.state, "correlation_id", None)
    org_id = claims["org"]
    
    cmd = ImproveWorkflowCommand(
        org_id=org_id,
        session_id=body.session_id,
        feedback=body.feedback
    )
    
    res = await container.planner_service.improve_workflow(cmd)
    if res.is_fail:
        raise HTTPException(status_code=422, detail=str(res.error()))
        
    wf = res.value()
    return {
        "data": {
            "workflow_id": wf.id,
            "name": wf.name,
            "status": wf.status.value,
            "nodes_count": len(wf.graph.nodes)
        },
        "meta": ResponseMeta(request_id=correlation_id)
    }

@router.post(
    "/explain",
    response_model=ResponseEnvelope[dict],
    summary="Explain selector choices, safety approvals, or structural limits of the plan"
)
async def explain_workflow(
    request: Request,
    body: WorkflowExplainRequest,
    claims: dict = Depends(verify_jwt)
) -> dict:
    from syncsphere.core.dependency_injection.container import container
    correlation_id = getattr(request.state, "correlation_id", None)
    org_id = claims["org"]
    
    cmd = ExplainWorkflowCommand(
        org_id=org_id,
        session_id=body.session_id
    )
    
    res = await container.planner_service.explain_workflow(cmd)
    if res.is_fail:
        raise HTTPException(status_code=422, detail=str(res.error()))
        
    return {
        "data": res.value(),
        "meta": ResponseMeta(request_id=correlation_id)
    }

@router.post(
    "/validate",
    response_model=ResponseEnvelope[dict],
    summary="Dry-run parsing validation of a planning prompt"
)
async def validate_prompt(
    request: Request,
    body: WorkflowValidateRequest,
    claims: dict = Depends(verify_jwt)
) -> dict:
    from syncsphere.core.dependency_injection.container import container
    correlation_id = getattr(request.state, "correlation_id", None)
    org_id = claims["org"]
    
    # We can validate using the IntentClassifier directly
    classifier = container.intent_classifier
    try:
        classification = await classifier.classify(org_id, body.prompt)
        return {
            "data": {
                "category": classification.category,
                "confidence": classification.confidence.confidence_score,
                "primary_goal": classification.primary_goal,
                "is_valid": classification.confidence.confidence_score > 0.5
            },
            "meta": ResponseMeta(request_id=correlation_id)
        }
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))

@router.get(
    "/preview",
    response_model=ResponseEnvelope[dict],
    summary="Preview the PlanAST structure or compiled topological execution order"
)
async def preview_plan(
    request: Request,
    session_id: str,
    claims: dict = Depends(verify_jwt)
) -> dict:
    from syncsphere.core.dependency_injection.container import container
    correlation_id = getattr(request.state, "correlation_id", None)
    org_id = claims["org"]
    
    query = PreviewWorkflowQuery(org_id=org_id, session_id=session_id)
    res = await container.planner_service.preview_workflow(query)
    if res.is_fail:
        raise HTTPException(status_code=422, detail=str(res.error()))
        
    return {
        "data": res.value(),
        "meta": ResponseMeta(request_id=correlation_id)
    }

@router.post(
    "/estimate",
    response_model=ResponseEnvelope[dict],
    summary="Retrieves estimated tokens execution costs and planning latency tallies"
)
async def estimate_plan(
    request: Request,
    body: WorkflowExplainRequest,
    claims: dict = Depends(verify_jwt)
) -> dict:
    from syncsphere.core.dependency_injection.container import container
    correlation_id = getattr(request.state, "correlation_id", None)
    org_id = claims["org"]
    
    cost_query = EstimateExecutionCostQuery(org_id=org_id, session_id=body.session_id)
    time_query = EstimateExecutionTimeQuery(org_id=org_id, session_id=body.session_id)
    
    cost_res = await container.planner_service.estimate_execution_cost(cost_query)
    time_res = await container.planner_service.estimate_execution_time(time_query)
    
    if cost_res.is_fail or time_res.is_fail:
        err = cost_res.error() if cost_res.is_fail else time_res.error()
        raise HTTPException(status_code=422, detail=str(err))
        
    return {
        "data": {
            "estimated_cost": cost_res.value(),
            "estimated_time_ms": time_res.value()
        },
        "meta": ResponseMeta(request_id=correlation_id)
    }
