from syncsphere.shared_kernel.domain.domain_exception import (
    DomainException,
    EntityNotFoundException,
    ValidationException,
    ConflictException,
    AuthorizationException,
    ExternalServiceException
)

class ConnectorDomainException(DomainException):
    """Base exception for all Connector domain errors."""
    pass

class ConnectorOfflineException(ExternalServiceException):
    """Raised when the target MCP server is unreachable or offline (HTTP 502)."""
    def __init__(self, connector_id: str, details: str = "") -> None:
        super().__init__(
            code="CONNECTOR_OFFLINE",
            message=f"MCP Connector '{connector_id}' is offline or unreachable. {details}",
            details={"connector_id": connector_id, "error": details}
        )

class ToolExecutionException(ExternalServiceException):
    """Raised when an MCP tools/call request returns an error or fails during execution (HTTP 502)."""
    def __init__(self, connector_id: str, tool_name: str, error_msg: str) -> None:
        super().__init__(
            code="TOOL_EXECUTION_FAILED",
            message=f"MCP Tool '{tool_name}' on connector '{connector_id}' failed: {error_msg}",
            details={"connector_id": connector_id, "tool_name": tool_name, "error": error_msg}
        )

class ToolNotFoundException(EntityNotFoundException):
    """Raised when the requested tool is not advertised in the connector's schema (HTTP 404)."""
    def __init__(self, connector_id: str, tool_name: str) -> None:
        super().__init__(
            code="TOOL_NOT_FOUND",
            message=f"Tool '{tool_name}' not found on connector '{connector_id}' schema.",
            details={"connector_id": connector_id, "tool_name": tool_name}
        )

class ConnectorRateLimitedException(ConnectorDomainException):
    """Raised when upstream API rate limits are breached (HTTP 429)."""
    def __init__(self, connector_id: str) -> None:
        super().__init__(
            code="CONNECTOR_RATE_LIMITED",
            message=f"Rate limit exceeded for connector '{connector_id}'.",
            status_code=429,
            details={"connector_id": connector_id}
        )

class DecryptionFailedException(ConnectorDomainException):
    """Raised when encrypted connector secrets fail base64 decryption (HTTP 500)."""
    def __init__(self, credential_id: str) -> None:
        super().__init__(
            code="DECRYPTION_FAILED",
            message=f"Failed to decrypt credentials for '{credential_id}'.",
            status_code=500,
            details={"credential_id": credential_id}
        )
