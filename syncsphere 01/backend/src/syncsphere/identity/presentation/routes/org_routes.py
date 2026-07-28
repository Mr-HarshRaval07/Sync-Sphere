import logging
from fastapi import APIRouter, Request, Depends, HTTPException
from syncsphere.shared_kernel.infrastructure.http.responses import ResponseEnvelope, ResponseMeta
from syncsphere.shared_kernel.infrastructure.http.dependencies import verify_jwt
from syncsphere.shared_kernel.domain.domain_exception import AuthorizationException, EntityNotFoundException
from syncsphere.identity.presentation.schemas import OrgResponse
from syncsphere.core.dependency_injection.container import container

logger = logging.getLogger("syncsphere.identity.presentation.routes.org_routes")

router = APIRouter(prefix="/organizations", tags=["Organizations"])

@router.get(
    "/current",
    response_model=ResponseEnvelope[OrgResponse],
    summary="Retrieve current organization tenant details"
)
async def get_current_org(request: Request, claims: dict = Depends(verify_jwt)) -> dict:
    correlation_id = getattr(request.state, "correlation_id", None)
    org_id = claims["org"]

    org = await container.org_repo.get_by_id(org_id)
    if not org:
        raise EntityNotFoundException("ORGANIZATION_NOT_FOUND", "Organization not found.")

    return {
        "data": OrgResponse(
            id=org.id,
            name=org.name,
            slug=org.slug,
            billing_tier=org.billing_tier,
            quotas=org.quotas,
            feature_flags=org.feature_flags
        ),
        "meta": ResponseMeta(request_id=correlation_id)
    }

@router.patch(
    "/current",
    response_model=ResponseEnvelope[OrgResponse],
    summary="Update organization configurations (Admin only)"
)
async def update_current_org(
    request: Request,
    body: dict, # Dynamic settings update
    claims: dict = Depends(verify_jwt)
) -> dict:
    correlation_id = getattr(request.state, "correlation_id", None)
    org_id = claims["org"]
    roles = claims.get("roles", [])

    if "ADMIN" not in roles:
        raise AuthorizationException("INSUFFICIENT_PERMISSIONS", "Admin role required to edit organization configurations.")

    org = await container.org_repo.get_by_id(org_id)
    if not org:
        raise EntityNotFoundException("ORGANIZATION_NOT_FOUND", "Organization not found.")

    # Update allowed fields
    if "name" in body:
        org.name = body["name"]
    if "settings" in body:
        org.settings.update(body["settings"])
        
    await container.org_repo.save(org)

    return {
        "data": OrgResponse(
            id=org.id,
            name=org.name,
            slug=org.slug,
            billing_tier=org.billing_tier,
            quotas=org.quotas,
            feature_flags=org.feature_flags
        ),
        "meta": ResponseMeta(request_id=correlation_id)
    }

@router.get(
    "/current/usage",
    response_model=ResponseEnvelope[dict],
    summary="Retrieve tenant resource usage against quotas"
)
async def get_usage(request: Request, claims: dict = Depends(verify_jwt)) -> dict:
    correlation_id = getattr(request.state, "correlation_id", None)
    org_id = claims["org"]

    org = await container.org_repo.get_by_id(org_id)
    if not org:
        raise EntityNotFoundException("ORGANIZATION_NOT_FOUND", "Organization not found.")

    # Calculate active usage (e.g. users count)
    user_count = await container.user_repo.count_by_org(org_id)

    return {
        "data": {
            "users": {
                "current": user_count,
                "limit": org.quotas.get("max_users", 5)
            },
            "workflows": {
                "current": 0, # Placeholder for workflows count
                "limit": org.quotas.get("max_workflows", 10)
            }
        },
        "meta": ResponseMeta(request_id=correlation_id)
    }
