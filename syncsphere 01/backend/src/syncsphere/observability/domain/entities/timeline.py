from typing import List, Optional
from syncsphere.shared_kernel.domain.aggregate_root import AggregateRoot
from syncsphere.observability.domain.value_objects import TimelineEvent

class AuditTimeline(AggregateRoot):
    def __init__(
        self,
        org_id: str,
        correlation_id: str,
        events: Optional[List[TimelineEvent]] = None,
        id: Optional[str] = None,
        **kwargs
    ) -> None:
        super().__init__(id=id, **kwargs)
        self.org_id = org_id
        self.correlation_id = correlation_id
        self.events = events or []

    def add_event(self, event: TimelineEvent) -> None:
        self.events.append(event)
        self.events.sort(key=lambda x: x.timestamp)
