from typing import Optional, List
from datetime import datetime
from syncsphere.shared_kernel.domain.aggregate_root import AggregateRoot
from syncsphere.observability.domain.value_objects import ServiceStatus

class HealthCheck(AggregateRoot):
    def __init__(
        self,
        org_id: str,
        services: Optional[List[ServiceStatus]] = None,
        id: Optional[str] = None,
        **kwargs
    ) -> None:
        super().__init__(id=id, **kwargs)
        self.org_id = org_id
        self.services = services or []
