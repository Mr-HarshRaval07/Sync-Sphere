from typing import Optional, Dict, Any
from datetime import datetime
from syncsphere.shared_kernel.domain.entity import Entity

class EventStoreEntry(Entity):
    def __init__(
        self,
        event_id: str,
        event_type: str,
        org_id: str,
        correlation_id: str,
        timestamp: Optional[datetime] = None,
        payload: Optional[Dict[str, Any]] = None,
        id: Optional[str] = None,
        **kwargs
    ) -> None:
        super().__init__(id=id, **kwargs)
        self.event_id = event_id
        self.event_type = event_type
        self.org_id = org_id
        self.correlation_id = correlation_id
        self.timestamp = timestamp or datetime.utcnow()
        self.payload = payload or {}
