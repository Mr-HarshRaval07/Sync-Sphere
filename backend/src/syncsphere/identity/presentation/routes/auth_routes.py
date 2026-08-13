import logging
from fastapi.responses import JSONResponse
from syncsphere.core.config.settings import settings
from fastapi import APIRouter, Request, status
from fastapi import APIRouter, HTTPException, Request, status
from syncsphere.core.config.app import Environment
from syncsphere.core.dependency_injection.container import container
from syncsphere.identity.presentation.schemas import (
    LoginRequest,
    RegisterRequest,
    TokenRefreshRequest,
    TokenResponse,
)
from syncsphere.shared_kernel.infrastructure.http.responses import (
    ResponseEnvelope,
    ResponseMeta,
)

logger = logging.getLogger(
    "syncsphere.identity.presentation.routes.auth_routes"
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=ResponseEnvelope[dict],
    status_code=status.HTTP_201_CREATED,
    summary="Register a new organization and admin user",
)
async def register(request: Request, body: RegisterRequest) -> dict:
    correlation_id = getattr(request.state, "correlation_id", None)

    result = await container.auth_service.register_user(
        email=body.email,
        password=body.password,
        first_name=body.first_name,
        last_name=body.last_name,
        org_name=body.org_name,
        org_slug=body.org_slug,
    )

    if result.is_fail:
        raise result.error()

    return {
        "data": {
            "user_id": result.value(),
            "status": "registered",
        },
        "meta": ResponseMeta(request_id=correlation_id),
    }

@router.post(
    "/login",
    response_model=ResponseEnvelope[TokenResponse],
    summary="Authenticate email and password",
)
async def login(request: Request, body: LoginRequest) -> dict:
    correlation_id = getattr(request.state, "correlation_id", None)

    user_agent = request.headers.get("User-Agent", "unknown")
    ip_address = request.client.host if request.client else "unknown"
    device_info = {
        "user_agent": user_agent,
        "ip_address": ip_address,
    }

    try:
        result = await container.auth_service.login(
            email=body.email,
            password=body.password,
            device_info=device_info,
        )

        if result.is_fail:
            logger.warning("Rejected login for email=%s", body.email)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password.",
            )

        access_token, refresh_token = result.value()

        response = JSONResponse(
            content={
                "data": {
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                },
                "meta": {
                    "request_id": correlation_id,
                },
            }
        )

        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=settings.app.environment in (Environment.STAGING, Environment.PRODUCTION),
            samesite="lax",
            max_age=settings.jwt_access_token_ttl,
            path="/",
        )

        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=settings.app.environment in (Environment.STAGING, Environment.PRODUCTION),
            samesite="lax",
            max_age=settings.jwt_refresh_token_ttl,
            path="/",
        )

        response.set_cookie(
            key="syncsphere-session",
            value="active",
            httponly=False,
            secure=settings.app.environment in (Environment.STAGING, Environment.PRODUCTION),
            samesite="lax",
            max_age=settings.jwt_refresh_token_ttl,
            path="/",
        )

        return response

    except HTTPException:
        raise
    except Exception:
        logger.exception("Login crashed for email=%s", body.email)
        raise
    
@router.post(
    "/refresh",
    response_model=ResponseEnvelope[TokenResponse],
    summary="Rotate refresh token and obtain new access token",
)
async def refresh(request: Request, body: TokenRefreshRequest) -> dict:
    correlation_id = getattr(request.state, "correlation_id", None)

    user_agent = request.headers.get("User-Agent", "unknown")
    ip_address = request.client.host if request.client else "unknown"
    device_info = {
        "user_agent": user_agent,
        "ip_address": ip_address,
    }

    refresh_token_to_use = body.refresh_token or request.cookies.get("refresh_token")
    if not refresh_token_to_use:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing refresh token."
        )

    result = await container.auth_service.refresh_access_token(
        raw_refresh_token=refresh_token_to_use,
        device_info=device_info,
    )

    if result.is_fail:
        raise result.error()

    access_token, refresh_token = result.value()

    response = JSONResponse(
        content={
            "data": {
                "access_token": access_token,
                "refresh_token": refresh_token,
            },
            "meta": {
                "request_id": correlation_id,
            },
        }
    )

    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=settings.app.environment in (Environment.STAGING, Environment.PRODUCTION),
        samesite="lax",
        max_age=settings.jwt_access_token_ttl,
        path="/",
    )

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=settings.app.environment in (Environment.STAGING, Environment.PRODUCTION),
        samesite="lax",
        max_age=settings.jwt_refresh_token_ttl,
        path="/",
    )

    response.set_cookie(
        key="syncsphere-session",
        value="active",
        httponly=False,
        secure=settings.app.environment in (Environment.STAGING, Environment.PRODUCTION),
        samesite="lax",
        max_age=settings.jwt_refresh_token_ttl,
        path="/",
    )

    return response


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Log out and revoke refresh token session",
)
async def logout(request: Request, body: TokenRefreshRequest = TokenRefreshRequest()):
    refresh_token_to_use = body.refresh_token or request.cookies.get("refresh_token")
    if refresh_token_to_use:
        result = await container.auth_service.logout(
            raw_refresh_token=refresh_token_to_use
        )
    
        if result.is_fail:
            raise result.error()
            
    response = JSONResponse(content={})
    response.status_code = status.HTTP_204_NO_CONTENT
    response.delete_cookie("access_token", path="/")
    response.delete_cookie("refresh_token", path="/")
    response.delete_cookie("syncsphere-session", path="/")
    return response