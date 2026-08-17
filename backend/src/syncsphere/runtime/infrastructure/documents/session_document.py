from pydantic import Field
from typing import List, Dict, Any, Optional
from syncsphere.shared_kernel.infrastructure.mongodb.base_document import BaseTenantDocument
from syncsphere.runtime.domain.value_objects import (
    ExecutionState,
    ExecutionPolicy,
    ExecutionStep,
    ExecutionMetrics,
    ExecutionCheckpoint,
    ExecutionHistory,
    ExecutionAST
)

class ExecutionSessionDocument(BaseTenantDocument):
    """Beanie ODM representation of the ExecutionSession aggregate root."""
    
    workflow_id: str
    version: int
    status: ExecutionState
    policy: ExecutionPolicy
    variables: Dict[str, Any] = Field(default_factory=dict)
    steps: Dict[str, ExecutionStep] = Field(default_factory=dict)
    checkpoints: List[ExecutionCheckpoint] = Field(default_factory=list)
    metrics: ExecutionMetrics = Field(default_factory=ExecutionMetrics)
    history: ExecutionHistory
    execution_ast: Optional[ExecutionAST] = None
    error_message: Optional[str] = None

    class Settings:
        name = "execution_sessions"
        indexes = [
            "org_id",
            "status",
            ("org_id", "workflow_id"),
            ("org_id", "status")
        ]
