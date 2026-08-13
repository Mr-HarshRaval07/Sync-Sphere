import logging
from fastapi import APIRouter, Request, Depends, status
from typing import List
from syncsphere.shared_kernel.infrastructure.http.responses import ResponseEnvelope, ResponseMeta, PaginatedResponseEnvelope
from syncsphere.shared_kernel.infrastructure.http.dependencies import verify_jwt
from syncsphere.shared_kernel.domain.domain_exception import AuthorizationException, EntityNotFoundException, ValidationException
from syncsphere.workflow.presentation.schemas import (
    CreateWorkflowRequest,
    UpdateWorkflowRequest,
    CloneWorkflowRequest,
    PublishWorkflowRequest,
    WorkflowResponse,
    WorkflowVersionResponse,
    ExecutionPlanResponse,
    ExecutionNodeSchema,
)
from syncsphere.core.dependency_injection.container import container
from syncsphere.workflow.infrastructure.dag.validator import DAGValidator
from syncsphere.workflow.domain.entities.workflow import Workflow

logger = logging.getLogger("syncsphere.workflow.presentation.routes.workflow_routes")

router = APIRouter(prefix="/workflows", tags=["Workflows"])

def map_workflow_to_response(wf) -> WorkflowResponse:
    """Helper to convert domain model to presentation response schema."""
    return WorkflowResponse(
        id=wf.id,
        name=wf.name,
        description=wf.description,
        status=wf.status,
        # state mirrors status: the frontend WorkflowCard checks workflow.state
        state=wf.status,
        nodes=wf.graph.nodes,
        edges=wf.graph.edges,
        variables=wf.variables,
        active_version=wf.active_version,
        latest_version=wf.latest_version
    )

@router.post(
    "",
    response_model=ResponseEnvelope[WorkflowResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create a new workflow configuration draft"
)
async def create(request: Request, body: CreateWorkflowRequest, claims: dict = Depends(verify_jwt)) -> dict:
    correlation_id = getattr(request.state, "correlation_id", None)
    org_id = claims["org"]

    result = await container.workflow_service.create_workflow(
        org_id=org_id,
        name=body.name,
        description=body.description,
        variables=body.variables
    )
    if result.is_fail:
        raise result.error()

    return {
        "data": map_workflow_to_response(result.value()),
        "meta": ResponseMeta(request_id=correlation_id)
    }

@router.get(
    "",
    response_model=PaginatedResponseEnvelope[WorkflowResponse],
    summary="List all active workflows in organization"
)
async def list_workflows(
    request: Request,
    page: int = 1,
    page_size: int = 20,
    claims: dict = Depends(verify_jwt)
) -> dict:
    correlation_id = getattr(request.state, "correlation_id", None)
    org_id = claims["org"]

    workflows = await container.workflow_repo.list_by_org(org_id, page, page_size)
    total_items = await container.workflow_repo.count_by_org(org_id)
    total_pages = (total_items + page_size - 1) // page_size

    data = [map_workflow_to_response(w) for w in workflows]

    return {
        "data": data,
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total_items": total_items,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_previous": page > 1
        },
        "meta": ResponseMeta(request_id=correlation_id)
    }

@router.get(
    "/{workflow_id}",
    response_model=ResponseEnvelope[WorkflowResponse],
    summary="Retrieve workflow details"
)
async def get_workflow(request: Request, workflow_id: str, claims: dict = Depends(verify_jwt)) -> dict:
    correlation_id = getattr(request.state, "correlation_id", None)
    org_id = claims["org"]

    workflow = await container.workflow_repo.get_by_id(workflow_id)
    if not workflow or workflow.org_id != org_id:
        raise EntityNotFoundException("WORKFLOW_NOT_FOUND", "Workflow not found.")

    return {
        "data": map_workflow_to_response(workflow),
        "meta": ResponseMeta(request_id=correlation_id)
    }

@router.patch(
    "/{workflow_id}",
    response_model=ResponseEnvelope[WorkflowResponse],
    summary="Update details, nodes and edges of a draft workflow"
)
async def update(
    request: Request,
    workflow_id: str,
    body: UpdateWorkflowRequest,
    claims: dict = Depends(verify_jwt)
) -> dict:
    correlation_id = getattr(request.state, "correlation_id", None)
    org_id = claims["org"]

    result = await container.workflow_service.update_workflow(
        org_id=org_id,
        workflow_id=workflow_id,
        name=body.name,
        description=body.description,
        nodes=body.nodes,
        edges=body.edges,
        variables=body.variables
    )
    if result.is_fail:
        raise result.error()

    return {
        "data": map_workflow_to_response(result.value()),
        "meta": ResponseMeta(request_id=correlation_id)
    }

@router.post(
    "/{workflow_id}/clone",
    response_model=ResponseEnvelope[WorkflowResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Clone a workflow draft blueprint"
)
async def clone(
    request: Request,
    workflow_id: str,
    body: CloneWorkflowRequest,
    claims: dict = Depends(verify_jwt)
) -> dict:
    correlation_id = getattr(request.state, "correlation_id", None)
    org_id = claims["org"]

    result = await container.workflow_service.clone_workflow(
        org_id=org_id,
        workflow_id=workflow_id,
        new_name=body.new_name
    )
    if result.is_fail:
        raise result.error()

    return {
        "data": map_workflow_to_response(result.value()),
        "meta": ResponseMeta(request_id=correlation_id)
    }

@router.post(
    "/{workflow_id}/publish",
    response_model=ResponseEnvelope[WorkflowVersionResponse],
    summary="Validate and publish a new workflow version snap"
)
async def publish(
    request: Request,
    workflow_id: str,
    body: PublishWorkflowRequest,
    claims: dict = Depends(verify_jwt)
) -> dict:
    correlation_id = getattr(request.state, "correlation_id", None)
    org_id = claims["org"]

    result = await container.workflow_service.publish_workflow(
        org_id=org_id,
        workflow_id=workflow_id,
        version_description=body.version_description
    )
    if result.is_fail:
        raise result.error()

    version = result.value()
    return {
        "data": WorkflowVersionResponse(
            id=version.id,
            workflow_id=version.workflow_id,
            version=version.version,
            description=version.description,
            state=version.state,
            nodes=version.graph.nodes,
            edges=version.graph.edges,
            variables=version.variables
        ),
        "meta": ResponseMeta(request_id=correlation_id)
    }

@router.get(
    "/{workflow_id}/versions",
    response_model=ResponseEnvelope[List[WorkflowVersionResponse]],
    summary="List all version history snapshots for a workflow"
)
async def list_versions(request: Request, workflow_id: str, claims: dict = Depends(verify_jwt)) -> dict:
    correlation_id = getattr(request.state, "correlation_id", None)
    org_id = claims["org"]

    workflow = await container.workflow_repo.get_by_id(workflow_id)
    if not workflow or workflow.org_id != org_id:
        raise EntityNotFoundException("WORKFLOW_NOT_FOUND", "Workflow not found.")

    versions = await container.version_repo.list_versions(workflow_id)

    data = [
        WorkflowVersionResponse(
            id=v.id,
            workflow_id=v.workflow_id,
            version=v.version,
            description=v.description,
            state=v.state,
            nodes=v.graph.nodes,
            edges=v.graph.edges,
            variables=v.variables
        ) for v in versions
    ]

    return {
        "data": data,
        "meta": ResponseMeta(request_id=correlation_id)
    }

@router.post(
    "/{workflow_id}/compile",
    response_model=ResponseEnvelope[ExecutionPlanResponse],
    summary="Compile graph and check topological dependencies"
)
async def compile_wf(request: Request, workflow_id: str, claims: dict = Depends(verify_jwt)) -> dict:
    correlation_id = getattr(request.state, "correlation_id", None)
    org_id = claims["org"]

    result = await container.workflow_service.compile_workflow(org_id, workflow_id)
    if result.is_fail:
        raise result.error()

    plan = result.value()
    
    execution_nodes_schema = {}
    for k, v in plan.execution_nodes.items():
        execution_nodes_schema[k] = ExecutionNodeSchema(
            node_id=v.node_id,
            name=v.name,
            type=v.type,
            dependencies=v.dependencies
        )

    return {
        "data": ExecutionPlanResponse(
            workflow_id=plan.workflow_id,
            version=plan.version,
            topological_order=plan.topological_order,
            execution_nodes=execution_nodes_schema
        ),
        "meta": ResponseMeta(request_id=correlation_id)
    }

@router.post(
    "/{workflow_id}/validate",
    response_model=ResponseEnvelope[dict],
    summary="Perform structural cycle and binding validation checks"
)
async def validate(request: Request, workflow_id: str, claims: dict = Depends(verify_jwt)) -> dict:
    correlation_id = getattr(request.state, "correlation_id", None)
    org_id = claims["org"]
    
    workflow = await container.workflow_repo.get_by_id(workflow_id)
    if not workflow or workflow.org_id != org_id:
        raise EntityNotFoundException("WORKFLOW_NOT_FOUND", "Workflow not found.")

    try:
        DAGValidator.validate(workflow.graph, workflow.variables)
        return {
            "data": {"valid": True, "message": "DAG structure and bindings successfully verified."},
            "meta": ResponseMeta(request_id=correlation_id)
        }
    except Exception as e:
        raise ValidationException("VALIDATION_FAILED", str(e))

@router.get(
    "/{workflow_id}/export",
    response_model=ResponseEnvelope[dict],
    summary="Export workflow configurations schema"
)
async def export_wf(request: Request, workflow_id: str, claims: dict = Depends(verify_jwt)) -> dict:
    correlation_id = getattr(request.state, "correlation_id", None)
    org_id = claims["org"]

    workflow = await container.workflow_repo.get_by_id(workflow_id)
    if not workflow or workflow.org_id != org_id:
        raise EntityNotFoundException("WORKFLOW_NOT_FOUND", "Workflow not found.")

    # Export mapping: simple serialization dump of nodes, edges and variables
    export_payload = {
        "name": workflow.name,
        "description": workflow.description,
        "nodes": {nid: n.model_dump() for nid, n in workflow.graph.nodes.items()},
        "edges": [e.model_dump() for e in workflow.graph.edges],
        "variables": [v.model_dump() for v in workflow.variables]
    }

    return {
        "data": export_payload,
        "meta": ResponseMeta(request_id=correlation_id)
    }

@router.post(
    "/import",
    response_model=ResponseEnvelope[WorkflowResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Import workflow configurations"
)
async def import_wf(request: Request, body: dict, claims: dict = Depends(verify_jwt)) -> dict:
    correlation_id = getattr(request.state, "correlation_id", None)
    org_id = claims["org"]

    # Validate import format keys
    required_keys = ["name", "nodes", "edges"]
    for key in required_keys:
        if key not in body:
            raise ValidationException("IMPORT_FORMAT_ERROR", f"Missing required import key: {key}")

    name = body["name"]
    description = body.get("description", "")
    
    # Parse nodes, edges and variables from payload
    from syncsphere.workflow.domain.value_objects import WorkflowNode, WorkflowEdge, Variable
    try:
        nodes = {nid: WorkflowNode(**n) for nid, n in body["nodes"].items()}
        edges = [WorkflowEdge(**e) for e in body["edges"]]
        variables = [Variable(**v) for v in body.get("variables", [])]
    except Exception as e:
        raise ValidationException("IMPORT_PARSE_ERROR", f"Failed to parse workflow definitions: {str(e)}")

    # Instantiate and save
    workflow = Workflow(
        org_id=org_id,
        name=name,
        description=description,
        variables=variables
    )
    workflow.graph.nodes = nodes
    workflow.graph.edges = edges

    await container.workflow_repo.save(workflow)

    return {
        "data": map_workflow_to_response(workflow),
        "meta": ResponseMeta(request_id=correlation_id)
    }

@router.delete(
    "/{workflow_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Archive a workflow"
)
async def delete_workflow(workflow_id: str, claims: dict = Depends(verify_jwt)) -> None:
    org_id = claims["org"]

    result = await container.workflow_service.archive_workflow(org_id, workflow_id)
    if result.is_fail:
        raise result.error()
