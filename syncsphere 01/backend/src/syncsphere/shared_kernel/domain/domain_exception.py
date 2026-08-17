from typing import Any, Dict, Optional

class DomainException(Exception):
    """Base exception class for all domain-specific errors in SyncSphere."""
    
    def __init__(
        self,
        code: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        status_code: int = 400,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details or {}
        self.status_code = status_code


class EntityNotFoundException(DomainException):
    """Raised when a requested resource is not found (HTTP 404)."""
    
    def __init__(
        self,
        code: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            code=code,
            message=message,
            details=details,
            status_code=404,
        )


class ValidationException(DomainException):
    """Raised when business validation rules or schemas fail (HTTP 400 / 422)."""
    
    def __init__(
        self,
        code: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        status_code: int = 422,
    ) -> None:
        super().__init__(
            code=code,
            message=message,
            details=details,
            status_code=status_code,
        )


class AuthorizationException(DomainException):
    """Raised when user lacks required permission (HTTP 403)."""
    
    def __init__(
        self,
        code: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            code=code,
            message=message,
            details=details,
            status_code=403,
        )


class ConflictException(DomainException):
    """Raised when resource state conflicts with the action (HTTP 409)."""
    
    def __init__(
        self,
        code: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            code=code,
            message=message,
            details=details,
            status_code=409,
        )


class RateLimitException(DomainException):
    """Raised when rate limits are exceeded (HTTP 429)."""
    
    def __init__(
        self,
        code: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            code=code,
            message=message,
            details=details,
            status_code=429,
        )


class ExternalServiceException(DomainException):
    """Raised when an external API or connector fails (HTTP 502)."""
    
    def __init__(
        self,
        code: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            code=code,
            message=message,
            details=details,
            status_code=502,
        )


class InfrastructureException(DomainException):
    """Raised when base infrastructure fails (HTTP 500)."""
    
    def __init__(
        self,
        code: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            code=code,
            message=message,
            details=details,
            status_code=500,
        )
