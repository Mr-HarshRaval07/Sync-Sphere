import logging
from fastapi import APIRouter, Request, Depends, HTTPException, status
from typing import List
from syncsphere.shared_kernel.infrastructure.http.responses import ResponseEnvelope, PaginatedResponseEnvelope, ResponseMeta
from syncsphere.shared_kernel.infrastructure.http.dependencies import verify_jwt
from syncsphere.shared_kernel.domain.domain_exception import AuthorizationException, EntityNotFoundException
from syncsphere.identity.presentation.schemas import (
    UserResponse,
    UpdateProfileRequest,
    InviteUserRequest,
    UpdateUserRequest,
    ApiKeyResponse,
    CreateApiKeyRequest,
    ApiKeyCreatedResponse
)
from syncsphere.core.dependency_injection.container import container
from syncsphere.identity.infrastructure.mappers import IdentityMappers
from syncsphere.identity.domain.entities.user import User

logger = logging.getLogger("syncsphere.identity.presentation.routes.user_routes")

router = APIRouter(prefix="/users", tags=["Users"])

# ==============================================================================
# Profile endpoints
# ==============================================================================

@router.get(
    "/me",
    response_model=ResponseEnvelope[UserResponse],
    summary="Retrieve profile of currently authenticated user"
)
async def get_me(request: Request, claims: dict = Depends(verify_jwt)) -> dict:
    correlation_id = getattr(request.state, "correlation_id", None)
    user_id = claims["sub"]
    
    user = await container.user_repo.get_by_id(user_id)
    if not user:
        raise EntityNotFoundException("USER_NOT_FOUND", "Logged-in user not found in data vault.")
        
    return {
        "data": UserResponse(
            id=user.id,
            org_id=user.org_id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            role_ids=user.role_ids,
            status=user.status,
            preferences={
                "default_google_sheets_id": user.preferences.default_google_sheets_id,
                "default_notion_db_id": user.preferences.default_notion_db_id
            } if getattr(user, "preferences", None) else None,
            created_at=user.created_at,
            updated_at=user.updated_at
        ),
        "meta": ResponseMeta(request_id=correlation_id)
    }

@router.patch(
    "/me",
    response_model=ResponseEnvelope[UserResponse],
    summary="Update profile fields of currently authenticated user"
)
async def update_me(request: Request, body: UpdateProfileRequest, claims: dict = Depends(verify_jwt)) -> dict:
    correlation_id = getattr(request.state, "correlation_id", None)
    user_id = claims["sub"]
    
    user = await container.user_repo.get_by_id(user_id)
    if not user:
        raise EntityNotFoundException("USER_NOT_FOUND", "Logged-in user not found in data vault.")
        
    if body.first_name is not None:
        user.first_name = body.first_name
    if body.last_name is not None:
        user.last_name = body.last_name
    if body.preferences is not None:
        if not hasattr(user, "preferences") or user.preferences is None:
            from syncsphere.identity.infrastructure.documents.user_document import UserPreferences
            user.preferences = UserPreferences()
        if body.preferences.default_google_sheets_id is not None:
            user.preferences.default_google_sheets_id = body.preferences.default_google_sheets_id
        if body.preferences.default_notion_db_id is not None:
            user.preferences.default_notion_db_id = body.preferences.default_notion_db_id
        
    await container.user_repo.save(user)
    
    return {
        "data": UserResponse(
            id=user.id,
            org_id=user.org_id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            role_ids=user.role_ids,
            status=user.status,
            preferences={
                "default_google_sheets_id": user.preferences.default_google_sheets_id,
                "default_notion_db_id": user.preferences.default_notion_db_id
            } if getattr(user, "preferences", None) else None,
            created_at=user.created_at,
            updated_at=user.updated_at
        ),
        "meta": ResponseMeta(request_id=correlation_id)
    }

# ==============================================================================
# Admin user management endpoints
# ==============================================================================

@router.get(
    "",
    response_model=PaginatedResponseEnvelope[UserResponse],
    summary="List members in organization (Admin only)"
)
async def list_users(
    request: Request,
    page: int = 1,
    page_size: int = 20,
    claims: dict = Depends(verify_jwt)
) -> dict:
    correlation_id = getattr(request.state, "correlation_id", None)
    org_id = claims["org"]
    roles = claims.get("roles", [])
    
    if "ADMIN" not in roles:
        raise AuthorizationException("INSUFFICIENT_PERMISSIONS", "Admin role required to view members list.")

    users_list = await container.user_repo.list_by_org(org_id, page, page_size)
    total_items = await container.user_repo.count_by_org(org_id)
    total_pages = (total_items + page_size - 1) // page_size

    data = [
        UserResponse(
            id=u.id,
            org_id=u.org_id,
            email=u.email,
            first_name=u.first_name,
            last_name=u.last_name,
            role_ids=u.role_ids,
            status=u.status,
            created_at=u.created_at,
            updated_at=u.updated_at
        ) for u in users_list
    ]

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

@router.post(
    "",
    response_model=ResponseEnvelope[UserResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Invite/create a new member in organization (Admin only)"
)
async def invite_user(request: Request, body: InviteUserRequest, claims: dict = Depends(verify_jwt)) -> dict:
    correlation_id = getattr(request.state, "correlation_id", None)
    org_id = claims["org"]
    roles = claims.get("roles", [])
    
    if "ADMIN" not in roles:
        raise AuthorizationException("INSUFFICIENT_PERMISSIONS", "Admin role required to invite members.")

    # Check duplicate email
    existing = await container.user_repo.get_by_email(body.email)
    if existing:
        from syncsphere.identity.domain.exceptions import DuplicateEmailException
        raise DuplicateEmailException(body.email)

    # Validate roles are valid role IDs in org
    for r_id in body.role_ids:
        r = await container.role_repo.get_by_id(r_id)
        if not r or r.org_id != org_id:
            raise EntityNotFoundException("ROLE_NOT_FOUND", f"Role ID '{r_id}' is invalid for this org.")

    # Create dummy password for invited user, since they will reset it on acceptance
    # In full flow, this triggers an invitation event
    user = User(
        org_id=org_id,
        email=body.email,
        password_hash=container.hasher.hash_password("temporary_invite_pass_123!"),
        first_name=body.first_name,
        last_name=body.last_name,
        role_ids=body.role_ids,
        status="ACTIVE"
    )
    await container.user_repo.save(user)

    return {
        "data": UserResponse(
            id=user.id,
            org_id=user.org_id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            role_ids=user.role_ids,
            status=user.status,
            created_at=user.created_at,
            updated_at=user.updated_at
        ),
        "meta": ResponseMeta(request_id=correlation_id)
    }

@router.patch(
    "/{user_id}",
    response_model=ResponseEnvelope[UserResponse],
    summary="Update roles/status of a member in organization (Admin only)"
)
async def update_user(
    request: Request,
    user_id: str,
    body: UpdateUserRequest,
    claims: dict = Depends(verify_jwt)
) -> dict:
    correlation_id = getattr(request.state, "correlation_id", None)
    org_id = claims["org"]
    roles = claims.get("roles", [])
    
    if "ADMIN" not in roles:
        raise AuthorizationException("INSUFFICIENT_PERMISSIONS", "Admin role required to edit members.")

    user = await container.user_repo.get_by_id(user_id)
    if not user or user.org_id != org_id:
        raise EntityNotFoundException("USER_NOT_FOUND", "User not found in organization.")

    if body.role_ids is not None:
        user.role_ids = body.role_ids
    if body.status is not None:
        user.status = body.status

    await container.user_repo.save(user)

    return {
        "data": UserResponse(
            id=user.id,
            org_id=user.org_id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            role_ids=user.role_ids,
            status=user.status,
            created_at=user.created_at,
            updated_at=user.updated_at
        ),
        "meta": ResponseMeta(request_id=correlation_id)
    }

@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Soft-delete a user member from organization (Admin only)"
)
async def delete_user(user_id: str, claims: dict = Depends(verify_jwt)) -> None:
    org_id = claims["org"]
    roles = claims.get("roles", [])
    
    if "ADMIN" not in roles:
        raise AuthorizationException("INSUFFICIENT_PERMISSIONS", "Admin role required to delete members.")

    user = await container.user_repo.get_by_id(user_id)
    if not user or user.org_id != org_id:
        raise EntityNotFoundException("USER_NOT_FOUND", "User not found in organization.")

    user.deactivate()
    await container.user_repo.save(user)

# ==============================================================================
# API Key management endpoints
# ==============================================================================

@router.get(
    "/{user_id}/api-keys",
    response_model=ResponseEnvelope[List[ApiKeyResponse]],
    summary="List API keys of a user"
)
async def list_api_keys(request: Request, user_id: str, claims: dict = Depends(verify_jwt)) -> dict:
    correlation_id = getattr(request.state, "correlation_id", None)
    org_id = claims["org"]
    caller_id = claims["sub"]
    roles = claims.get("roles", [])
    
    # User can list own keys, Admin can list anyone's keys
    if caller_id != user_id and "ADMIN" not in roles:
        raise AuthorizationException("INSUFFICIENT_PERMISSIONS", "Access denied.")

    keys = await container.api_key_repo.list_by_user(org_id, user_id)
    data = [
        ApiKeyResponse(
            id=k.id,
            name=k.name,
            key_prefix=k.key_prefix,
            scopes=k.scopes,
            expires_at=k.expires_at,
            status=k.status
        ) for k in keys
    ]

    return {
        "data": data,
        "meta": ResponseMeta(request_id=correlation_id)
    }

@router.post(
    "/{user_id}/api-keys",
    response_model=ResponseEnvelope[ApiKeyCreatedResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Generate a new API key for a user"
)
async def create_api_key(
    request: Request,
    user_id: str,
    body: CreateApiKeyRequest,
    claims: dict = Depends(verify_jwt)
) -> dict:
    correlation_id = getattr(request.state, "correlation_id", None)
    org_id = claims["org"]
    caller_id = claims["sub"]
    roles = claims.get("roles", [])
    
    if caller_id != user_id and "ADMIN" not in roles:
        raise AuthorizationException("INSUFFICIENT_PERMISSIONS", "Access denied.")

    result = await container.auth_service.rotate_api_key(
        org_id=org_id,
        user_id=user_id,
        name=body.name,
        scopes=body.scopes,
        expires_in_days=body.expires_in_days
    )
    if result.is_fail:
        raise result.error()

    raw_key, api_key = result.value()

    return {
        "data": ApiKeyCreatedResponse(
            id=api_key.id,
            name=api_key.name,
            raw_key=raw_key,
            key_prefix=api_key.key_prefix,
            scopes=api_key.scopes,
            expires_at=api_key.expires_at
        ),
        "meta": ResponseMeta(request_id=correlation_id)
    }

@router.delete(
    "/{user_id}/api-keys/{key_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoke an API key of a user"
)
async def revoke_api_key(user_id: str, key_id: str, claims: dict = Depends(verify_jwt)) -> None:
    org_id = claims["org"]
    caller_id = claims["sub"]
    roles = claims.get("roles", [])
    
    if caller_id != user_id and "ADMIN" not in roles:
        raise AuthorizationException("INSUFFICIENT_PERMISSIONS", "Access denied.")

    api_key = await container.api_key_repo.get_by_id(key_id)
    if not api_key or api_key.org_id != org_id or api_key.user_id != user_id:
        raise EntityNotFoundException("API_KEY_NOT_FOUND", "API key not found.")

    api_key.revoke()
    await container.api_key_repo.save(api_key)
