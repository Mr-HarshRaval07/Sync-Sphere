from syncsphere.shared_kernel.domain.domain_exception import (
    DomainException,
    EntityNotFoundException,
    ValidationException
)

class ExecutionSessionNotFoundException(EntityNotFoundException):
    """Raised when an requested execution session is not found in database (HTTP 404)."""
    def __init__(self, session_id: str) -> None:
        super().__init__(
            code="EXECUTION_SESSION_NOT_FOUND",
            message=f"Execution session '{session_id}' not found.",
            details={"session_id": session_id}
        )

class InvalidStateTransitionException(ValidationException):
    """Raised when trying to perform an invalid state transition (HTTP 422)."""
    def __init__(self, message: str) -> None:
        super().__init__(
            code="INVALID_STATE_TRANSITION",
            message=message
        )

class LockAcquisitionException(ValidationException):
    """Raised when trying to acquire a lock that is already held by another owner (HTTP 422)."""
    def __init__(self, lock_key: str, message: str = "Lock already held.") -> None:
        super().__init__(
            code="LOCK_ACQUISITION_FAILED",
            message=f"Unable to acquire lock '{lock_key}': {message}",
            details={"lock_key": lock_key}
        )

class LeaseExpiredException(ValidationException):
    """Raised when trying to use or renew an expired worker lease (HTTP 422)."""
    def __init__(self, lease_id: str) -> None:
        super().__init__(
            code="LEASE_EXPIRED",
            message=f"Lease '{lease_id}' has expired.",
            details={"lease_id": lease_id}
        )

class SagaCompensationException(ValidationException):
    """Raised when compensation logic fails during Saga rollbacks (HTTP 422)."""
    def __init__(self, session_id: str, message: str) -> None:
        super().__init__(
            code="SAGA_COMPENSATION_FAILED",
            message=f"Saga compensation for session '{session_id}' failed: {message}",
            details={"session_id": session_id}
        )
