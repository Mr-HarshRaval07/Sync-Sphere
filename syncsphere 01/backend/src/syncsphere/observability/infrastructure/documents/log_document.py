from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import Field
from syncsphere.shared_kernel.infrastructure.mongodb.base_document import BaseTenantDocument

class StructuredLogDocument(BaseTenantDocument):
    correlation_id: str
    message: str
    level: str = "INFO"
    module: str = "observability"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    context_info: Dict[str, Any] = Field(default_factory=dict)

    class Settings:
        name = "observability_structured_logs"
        indexes = [
            "org_id",
            "correlation_id",
            "level",
            "timestamp"
        ]
