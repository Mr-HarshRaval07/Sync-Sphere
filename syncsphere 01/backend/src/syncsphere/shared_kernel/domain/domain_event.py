import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class DomainEvent(BaseModel):
    """
    Base class representing domain events occurring inside aggregate boundaries.
    Does not depend on any outer infrastructure layer.
    """
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique ID for this event occurrence")
    event_type: str = Field(..., description="String classification of the event name")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Time of event occurrence")
    org_id: str = Field(..., description="Tenant organization scope identifier")
    correlation_id: Optional[str] = Field(default=None, description="Correlation request tracing ID")
