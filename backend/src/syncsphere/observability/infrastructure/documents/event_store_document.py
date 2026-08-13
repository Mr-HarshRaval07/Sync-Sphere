from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import Field
from syncsphere.shared_kernel.infrastructure.mongodb.base_document import BaseTenantDocument

class EventStoreEntryDocument(BaseTenantDocument):
    event_id: str
    event_type: str
    correlation_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    payload: Dict[str, Any] = Field(default_factory=dict)

    class Settings:
        name = "observability_event_store"
        indexes = [
            "org_id",
            "event_id",
            "event_type",
            "correlation_id",
            "timestamp"
        ]
