from syncsphere.shared_kernel.domain.domain_exception import (
    DomainException,
    EntityNotFoundException,
    ValidationException,
    ConflictException
)

class WorkflowDomainException(DomainException):
    """Base exception for all Workflow domain errors."""
    pass

class WorkflowNotFoundException(EntityNotFoundException):
    """Raised when a workflow ID does not exist in the database (HTTP 404)."""
    def __init__(self, workflow_id: str) -> None:
        super().__init__(
            code="WORKFLOW_NOT_FOUND",
            message=f"Workflow with ID '{workflow_id}' not found.",
            details={"workflow_id": workflow_id}
        )

class InvalidWorkflowGraphException(ValidationException):
    """Raised when a Directed Acyclic Graph (DAG) validation check fails, e.g. cycles (HTTP 400)."""
    def __init__(self, message: str, details: dict = None) -> None:
        super().__init__(
            code="INVALID_WORKFLOW_GRAPH",
            message=message,
            details=details or {}
        )

class VariableResolutionException(ValidationException):
    """Raised when workflow expressions reference undefined variables (HTTP 400)."""
    def __init__(self, variable_name: str, message: str = "") -> None:
        super().__init__(
            code="VARIABLE_RESOLUTION_FAILED",
            message=message or f"Variable '{variable_name}' could not be resolved in the current context.",
            details={"variable_name": variable_name}
        )

class WorkflowVersionConflictException(ConflictException):
    """Raised when trying to publish/save a version that already exists or conflicts (HTTP 409)."""
    def __init__(self, workflow_id: str, version: int) -> None:
        super().__init__(
            code="WORKFLOW_VERSION_CONFLICT",
            message=f"Conflict saving version '{version}' for workflow '{workflow_id}'.",
            details={"workflow_id": workflow_id, "version": version}
        )
