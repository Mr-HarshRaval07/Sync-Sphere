from typing import List, Optional, Dict, Any
from pydantic import Field
from datetime import datetime
from syncsphere.shared_kernel.infrastructure.mongodb.base_document import BaseTenantDocument
from syncsphere.observability.domain.value_objects import TraceSpanVO

class TraceDocument(BaseTenantDocument):
    correlation_id: str = Field(..., description="Tracing correlation ID")
    spans: List[TraceSpanVO] = Field(default_factory=list)

    class Settings:
        name = "observability_traces"
        indexes = [
            "org_id",
            "correlation_id",
            "created_at"
        ]
