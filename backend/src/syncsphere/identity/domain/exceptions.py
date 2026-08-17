from syncsphere.shared_kernel.domain.domain_exception import (
    DomainException,
    EntityNotFoundException,
    ValidationException,
    ConflictException,
    AuthorizationException
)
from typing import Any, Dict, Optional

class IdentityException(DomainException):
    """Base exception for all Identity domain errors."""
    pass

class AuthenticationFailedException(IdentityException):
    """Raised when authentication credentials are invalid (HTTP 401)."""
    def __init__(self, message: str = "Invalid email or password.") -> None:
        super().__init__(code="AUTH_INVALID_CREDENTIALS", message=message, status_code=401)

class TokenExpiredException(IdentityException):
    """Raised when a JWT access or refresh token has expired (HTTP 401)."""
    def __init__(self, message: str = "Token has expired.") -> None:
        super().__init__(code="AUTH_TOKEN_EXPIRED", message=message, status_code=401)

class TokenInvalidException(IdentityException):
    """Raised when a JWT token signature is invalid or malformed (HTTP 401)."""
    def __init__(self, message: str = "Token signature verification failed.") -> None:
        super().__init__(code="AUTH_TOKEN_INVALID", message=message, status_code=401)

class RefreshTokenReusedException(IdentityException):
    """Raised when token reuse/replay attack is detected (HTTP 401)."""
    def __init__(self, message: str = "Token reuse detected. Session revoked.") -> None:
        super().__init__(code="AUTH_REFRESH_TOKEN_REUSED", message=message, status_code=401)

class UserDeactivatedException(IdentityException):
    """Raised when trying to authenticate or execute operations as a deactivated user (HTTP 403)."""
    def __init__(self, message: str = "This user account is suspended/deactivated.") -> None:
        super().__init__(code="USER_DEACTIVATED", message=message, status_code=403)

class DuplicateEmailException(ConflictException):
    """Raised when registering an email that already exists (HTTP 409)."""
    def __init__(self, email: str) -> None:
        super().__init__(
            code="DUPLICATE_EMAIL",
            message=f"Email address '{email}' is already registered.",
            details={"email": email}
        )

class DuplicateRoleException(ConflictException):
    """Raised when creating a role name that already exists (HTTP 409)."""
    def __init__(self, role_name: str) -> None:
        super().__init__(
            code="DUPLICATE_ROLE",
            message=f"Role with name '{role_name}' already exists.",
            details={"role_name": role_name}
        )

class OrganizationQuotaExceededException(IdentityException):
    """Raised when trying to exceed organization quota limits (HTTP 403)."""
    def __init__(self, quota_name: str, limit: int) -> None:
        super().__init__(
            code="QUOTA_EXCEEDED",
            message=f"Organization quota exceeded for '{quota_name}'. Limit is {limit}.",
            details={"quota_name": quota_name, "limit": limit},
            status_code=403
        )
