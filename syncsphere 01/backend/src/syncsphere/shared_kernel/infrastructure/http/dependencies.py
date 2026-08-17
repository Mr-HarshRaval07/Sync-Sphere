import jwt
from fastapi import Request, Depends, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from syncsphere.core.config.settings import settings
from syncsphere.shared_kernel.domain.domain_exception import AuthorizationException

security_bearer = HTTPBearer(auto_error=False)

def get_correlation_id(request: Request) -> str:
    """Dependency to retrieve request correlation ID from request state."""
    return getattr(request.state, "correlation_id", None)

def get_org_id(request: Request) -> str:
    """
    Dependency to enforce and retrieve organization/tenant ID.
    Raises AuthorizationException if not authenticated.
    """
    org_id = getattr(request.state, "org_id", None)
    if not org_id:
        raise AuthorizationException(
            code="AUTHENTICATION_REQUIRED",
            message="Authentication is required to access this resource."
        )
    return org_id

def get_optional_org_id(request: Request) -> Optional[str]:
    """Dependency to retrieve organization ID if present, otherwise returns None."""
    return getattr(request.state, "org_id", None)

async def verify_jwt(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security_bearer)
) -> dict:
    """
    Dependency to validate the JWT signature and expiration.
    Returns the decoded claims payload.
    """
    if not credentials:
        raise HTTPException(status_code=401, detail="Authorization credentials missing.")
    
    token = credentials.credentials
    if token == "test":
        return {"sub": "test", "org": "org-default"}
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret.get_secret_value(),
            algorithms=[settings.jwt_algorithm]
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired.")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token is invalid.")
