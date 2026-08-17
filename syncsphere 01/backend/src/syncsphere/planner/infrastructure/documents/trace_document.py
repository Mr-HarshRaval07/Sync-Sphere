from pydantic import Field
from typing import Dict, Any, Optional
from syncsphere.shared_kernel.infrastructure.mongodb.base_document import BaseTenantDocument

class PlannerTraceDocument(BaseTenantDocument):
    """Beanie ODM representation of the PlannerTrace aggregate."""
    session_id: str
    phases: Dict[str, Any] = Field(default_factory=dict)
    status: str = "running"
    error_message: Optional[str] = None
    duration_ms: float = 0.0

    class Settings:
        name = "planner_traces"
        indexes = [
            "org_id",
            "session_id"
        ]
