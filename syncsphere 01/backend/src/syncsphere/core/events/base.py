from pydantic import Field
from syncsphere.shared_kernel.domain.domain_event import DomainEvent

class BaseEvent(DomainEvent):
    """
    Standard base class representing system-wide domain and integration events.
    Inherits fields from domain layer and maps them to message-bus contracts.
    """
    # Enforce correlation_id as required on integration event bus boundaries
    correlation_id: str = Field(..., description="Request tracing correlation ID")
