from typing import Optional, Dict, Any
from syncsphere.shared_kernel.domain.domain_exception import EntityNotFoundException, ValidationException

class TraceNotFoundException(EntityNotFoundException):
    def __init__(self, trace_id: str, details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(
            code="TRACE_NOT_FOUND",
            message=f"Trace with ID '{trace_id}' was not found.",
            details=details
        )

class ReplayFailedException(ValidationException):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(
            code="REPLAY_FAILED",
            message=message,
            details=details
        )

class AlertNotFoundException(EntityNotFoundException):
    def __init__(self, alert_id: str, details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(
            code="ALERT_NOT_FOUND",
            message=f"Alert with ID '{alert_id}' was not found.",
            details=details
        )
