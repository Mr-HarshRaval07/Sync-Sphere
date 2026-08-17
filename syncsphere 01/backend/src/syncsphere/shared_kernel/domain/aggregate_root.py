from typing import List, Any
from .entity import Entity
from .domain_event import DomainEvent

class AggregateRoot(Entity):
    """
    Base class for all aggregate roots in SyncSphere.
    Maintains list of uncommitted domain events that occurred during transaction.
    """
    
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._domain_events: List[DomainEvent] = []

    def add_domain_event(self, event: DomainEvent) -> None:
        """Records a domain event that occurred inside the aggregate boundary."""
        self._domain_events.append(event)

    def clear_domain_events(self) -> None:
        """Clears the list of uncommitted domain events."""
        self._domain_events.clear()

    def get_domain_events(self) -> List[DomainEvent]:
        """Retrieves a read-only list of uncommitted domain events."""
        return list(self._domain_events)
