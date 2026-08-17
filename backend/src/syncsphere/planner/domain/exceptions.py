from syncsphere.shared_kernel.domain.domain_exception import (
    DomainException,
    EntityNotFoundException,
    ValidationException,
    ExternalServiceException
)

class SessionNotFoundException(EntityNotFoundException):
    """Raised when an requested planning session is not found in database (HTTP 404)."""
    def __init__(self, session_id: str) -> None:
        super().__init__(
            code="SESSION_NOT_FOUND",
            message=f"Planning session '{session_id}' not found.",
            details={"session_id": session_id}
        )

class PlanningFailedException(ValidationException):
    """Raised when the planning pipeline is unable to decompose or compile a plan (HTTP 422)."""
    def __init__(self, message: str) -> None:
        super().__init__(
            code="PLANNING_FAILED",
            message=f"Planning failed: {message}"
        )

class SafetyViolationException(ValidationException):
    """Raised when a plan violates cost quotas, cycles, or other critical constraints (HTTP 422)."""
    def __init__(self, message: str) -> None:
        super().__init__(
            code="SAFETY_VIOLATION",
            message=f"Plan violates safety constraints: {message}"
        )

class LowConfidenceException(ValidationException):
    """Raised when intent classification or tool matching scores fall below safety thresholds (HTTP 422)."""
    def __init__(self, score: float, threshold: float, message: str) -> None:
        super().__init__(
            code="LOW_CONFIDENCE",
            message=f"Planner confidence too low ({score} < threshold {threshold}): {message}",
            details={"confidence_score": score, "threshold": threshold}
        )
