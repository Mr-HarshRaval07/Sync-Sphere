import logging
from fastapi import APIRouter, Request, Depends, status
from typing import List
from syncsphere.shared_kernel.infrastructure.http.responses import ResponseEnvelope, ResponseMeta
from syncsphere.shared_kernel.infrastructure.http.dependencies import verify_jwt
from syncsphere.shared_kernel.domain.domain_exception import AuthorizationException, EntityNotFoundException
from syncsphere.connectors.presentation.schemas import (
    RegisterConnectorRequest,
    ConnectorResponse,
    UpdateCredentialRequest,
    CallToolRequest,
    ToolResultResponse,
    ToolDefinitionSchema,
    ConnectorHealthSchema,
)
from syncsphere.core.dependency_injection.container import container

logger = logging.getLogger("syncsphere.connectors.presentation.routes.connector_routes")

router = APIRouter(prefix="/connectors", tags=["Connectors"])

def map_connector_to_response(conn) -> ConnectorResponse:
    """Helper to convert domain model to presentation response schema."""
    return ConnectorResponse(
        id=conn.id,
        name=conn.name,
        transport_type=conn.transport_type,
        connection_config=conn.connection_config,
        status=conn.status,
        tools=[
            ToolDefinitionSchema(
                name=t.name,
                description=t.description,
                input_schema=t.input_schema
            ) for t in conn.tools
        ],
        max_requests_per_minute=conn.limits.max_requests_per_minute,
        health=ConnectorHealthSchema(
            status=conn.health.status,
            latency_ms=conn.health.latency_ms,
            last_checked=conn.health.last_checked,
            error_message=conn.health.error_message
        )
    )

@router.post(
    "",
    response_model=ResponseEnvelope[ConnectorResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Register a new Model Context Protocol connector config"
)
async def register(request: Request, body: RegisterConnectorRequest, claims: dict = Depends(verify_jwt)) -> dict:
    correlation_id = getattr(request.state, "correlation_id", None)
    org_id = claims["org"]
    roles = claims.get("roles", [])

    if "ADMIN" not in roles:
        raise AuthorizationException("INSUFFICIENT_PERMISSIONS", "Admin role required to register connectors.")

    result = await container.connector_service.register_connector(
        org_id=org_id,
        name=body.name,
        transport_type=body.transport_type,
        connection_config=body.connection_config,
        max_requests_per_minute=body.max_requests_per_minute,
        required_scopes=body.required_scopes
    )
    if result.is_fail:
        raise result.error()

    return {
        "data": map_connector_to_response(result.value()),
        "meta": ResponseMeta(request_id=correlation_id)
    }

@router.get(
    "",
    response_model=ResponseEnvelope[List[ConnectorResponse]],
    summary="List all registered connectors in organization"
)
async def list_connectors(request: Request, claims: dict = Depends(verify_jwt)) -> dict:
    correlation_id = getattr(request.state, "correlation_id", None)
    org_id = claims["org"]

    connectors = await container.connector_repo.list_by_org(org_id)
    data = [map_connector_to_response(c) for c in connectors]

    return {
        "data": data,
        "meta": ResponseMeta(request_id=correlation_id)
    }

@router.get(
    "/{connector_id}",
    response_model=ResponseEnvelope[ConnectorResponse],
    summary="Retrieve connector profile and capabilities schema"
)
async def get_connector(request: Request, connector_id: str, claims: dict = Depends(verify_jwt)) -> dict:
    correlation_id = getattr(request.state, "correlation_id", None)
    org_id = claims["org"]

    connector = await container.connector_repo.get_by_id(connector_id)
    if not connector or connector.org_id != org_id:
        raise EntityNotFoundException("CONNECTOR_NOT_FOUND", "Connector not found.")

    return {
        "data": map_connector_to_response(connector),
        "meta": ResponseMeta(request_id=correlation_id)
    }

@router.post(
    "/{connector_id}/credentials",
    response_model=ResponseEnvelope[dict],
    summary="Configure/rotate API keys and secrets for connector"
)
async def update_credentials(
    request: Request,
    connector_id: str,
    body: UpdateCredentialRequest,
    claims: dict = Depends(verify_jwt)
) -> dict:
    correlation_id = getattr(request.state, "correlation_id", None)
    org_id = claims["org"]
    roles = claims.get("roles", [])

    if "ADMIN" not in roles:
        raise AuthorizationException("INSUFFICIENT_PERMISSIONS", "Admin role required to configure credentials.")

    result = await container.connector_service.update_credentials(
        org_id=org_id,
        connector_id=connector_id,
        raw_secrets=body.secrets
    )
    if result.is_fail:
        raise result.error()

    return {
        "data": {"status": "credentials_updated"},
        "meta": ResponseMeta(request_id=correlation_id)
    }

@router.post(
    "/{connector_id}/sync",
    response_model=ResponseEnvelope[ConnectorResponse],
    summary="Force synchronize and re-handshake tools schema metadata"
)
async def sync_capabilities(request: Request, connector_id: str, claims: dict = Depends(verify_jwt)) -> dict:
    correlation_id = getattr(request.state, "correlation_id", None)
    org_id = claims["org"]

    result = await container.connector_service.sync_capabilities(org_id, connector_id)
    if result.is_fail:
        raise result.error()

    connector = await container.connector_repo.get_by_id(connector_id)
    return {
        "data": map_connector_to_response(connector),
        "meta": ResponseMeta(request_id=correlation_id)
    }

@router.post(
    "/{connector_id}/tools/{tool_name}/call",
    response_model=ResponseEnvelope[ToolResultResponse],
    summary="Invoke an MCP tool call payload"
)
async def call_tool(
    request: Request,
    connector_id: str,
    tool_name: str,
    body: CallToolRequest,
    claims: dict = Depends(verify_jwt)
) -> dict:
    correlation_id = getattr(request.state, "correlation_id", None)
    org_id = claims["org"]

    # In a production system, we evaluate if caller's JWT role matches the allowed connector permissions.
    # For now, standard org-level auth checks are enforced.
    
    result = await container.connector_service.execute_tool(
        org_id=org_id,
        connector_id=connector_id,
        tool_name=tool_name,
        arguments=body.arguments
    )
    if result.is_fail:
        raise result.error()

    res = result.value()
    return {
        "data": ToolResultResponse(
            content=res.content,
            is_error=res.is_error
        ),
        "meta": ResponseMeta(request_id=correlation_id)
    }

@router.delete(
    "/{connector_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a connector configuration"
)
async def delete_connector(connector_id: str, claims: dict = Depends(verify_jwt)) -> None:
    org_id = claims["org"]
    roles = claims.get("roles", [])

    if "ADMIN" not in roles:
        raise AuthorizationException("INSUFFICIENT_PERMISSIONS", "Admin role required to delete connectors.")

    connector = await container.connector_repo.get_by_id(connector_id)
    if not connector or connector.org_id != org_id:
        raise EntityNotFoundException("CONNECTOR_NOT_FOUND", "Connector not found.")

    await container.connector_loader.close_client(connector_id)
    await container.connector_repo.delete(connector_id)
    await container.connector_credential_repo.delete(org_id, connector_id)
