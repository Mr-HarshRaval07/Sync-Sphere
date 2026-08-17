import logging
from fastapi import APIRouter, Request, Depends, HTTPException, status
from typing import List
from syncsphere.shared_kernel.infrastructure.http.responses import ResponseEnvelope, ResponseMeta
from syncsphere.shared_kernel.infrastructure.http.dependencies import verify_jwt
from syncsphere.shared_kernel.domain.domain_exception import AuthorizationException, EntityNotFoundException
from syncsphere.identity.presentation.schemas import RoleResponse, CreateRoleRequest, PermissionSchema
from syncsphere.identity.domain.entities.permission import Permission
from syncsphere.core.dependency_injection.container import container

logger = logging.getLogger("syncsphere.identity.presentation.routes.role_routes")

router = APIRouter(prefix="/roles", tags=["Roles"])

@router.get(
    "",
    response_model=ResponseEnvelope[List[RoleResponse]],
    summary="List all configured roles in organization"
)
async def list_roles(request: Request, claims: dict = Depends(verify_jwt)) -> dict:
    correlation_id = getattr(request.state, "correlation_id", None)
    org_id = claims["org"]

    roles = await container.role_repo.list_by_org(org_id)
    data = [
        RoleResponse(
            id=r.id,
            org_id=r.org_id,
            name=r.name,
            description=r.description,
            is_system_role=r.is_system_role,
            permissions=[
                PermissionSchema(
                    resource_type=p.resource_type,
                    resource_id=p.resource_id,
                    actions=p.actions
                ) for p in r.permissions
            ]
        ) for r in roles
    ]

    return {
        "data": data,
        "meta": ResponseMeta(request_id=correlation_id)
    }

@router.post(
    "",
    response_model=ResponseEnvelope[RoleResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create a custom security role for the tenant (Admin only)"
)
async def create_role(
    request: Request,
    body: CreateRoleRequest,
    claims: dict = Depends(verify_jwt)
) -> dict:
    correlation_id = getattr(request.state, "correlation_id", None)
    org_id = claims["org"]
    caller_roles = claims.get("roles", [])

    if "ADMIN" not in caller_roles:
        raise AuthorizationException("INSUFFICIENT_PERMISSIONS", "Admin role required to create custom roles.")

    # Convert schema permissions to domain permissions
    domain_permissions = [
        Permission(
            resource_type=p.resource_type,
            resource_id=p.resource_id,
            actions=p.actions
        ) for p in body.permissions
    ]

    result = await container.rbac_service.create_role(
        org_id=org_id,
        name=body.name.upper(),
        description=body.description,
        permissions=domain_permissions
    )
    if result.is_fail:
        raise result.error()

    role = result.value()

    return {
        "data": RoleResponse(
            id=role.id,
            org_id=role.org_id,
            name=role.name,
            description=role.description,
            is_system_role=role.is_system_role,
            permissions=[
                PermissionSchema(
                    resource_type=p.resource_type,
                    resource_id=p.resource_id,
                    actions=p.actions
                ) for p in role.permissions
            ]
        ),
        "meta": ResponseMeta(request_id=correlation_id)
    }

@router.delete(
    "/{role_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a custom role (Admin only)"
)
async def delete_role(role_id: str, claims: dict = Depends(verify_jwt)) -> None:
    org_id = claims["org"]
    caller_roles = claims.get("roles", [])

    if "ADMIN" not in caller_roles:
        raise AuthorizationException("INSUFFICIENT_PERMISSIONS", "Admin role required to delete custom roles.")

    role = await container.role_repo.get_by_id(role_id)
    if not role or role.org_id != org_id:
        raise EntityNotFoundException("ROLE_NOT_FOUND", "Role not found.")

    if role.is_system_role:
        raise AuthorizationException("CANNOT_DELETE_SYSTEM_ROLE", "System roles are immutable and cannot be deleted.")

    await container.role_repo.delete(role_id)
