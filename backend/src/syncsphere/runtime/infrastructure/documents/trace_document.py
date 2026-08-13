from pydantic import Field
from typing import Dict, Any, List, Optional
from syncsphere.shared_kernel.infrastructure.mongodb.base_document import BaseTenantDocument

class ExecutionTraceDocument(BaseTenantDocument):
    """Beanie ODM representation of the ExecutionTrace aggregate tracking multi-phase execution logs."""
    
    session_id: str
    phases: Dict[str, List[Dict[str, Any]]] = Field(default_factory=dict)
    status: str
    duration_ms: float = 0.0

    class Settings:
        name = "execution_traces"
        indexes = [
            "org_id",
            "session_id"
        ]
