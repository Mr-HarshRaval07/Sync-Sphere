from typing import Optional, Dict, Any
from datetime import datetime
from syncsphere.shared_kernel.domain.aggregate_root import AggregateRoot

class Alert(AggregateRoot):
    def __init__(
        self,
        org_id: str,
        name: str,
        message: str,
        severity: str = "WARNING",
        status: str = "ACTIVE",
        metric_name: Optional[str] = None,
        resolved_at: Optional[datetime] = None,
        id: Optional[str] = None,
        **kwargs
    ) -> None:
        super().__init__(id=id, **kwargs)
        self.org_id = org_id
        self.name = name
        self.message = message
        self.severity = severity
        self.status = status
        self.metric_name = metric_name
        self.resolved_at = resolved_at

    def resolve(self) -> None:
        self.status = "RESOLVED"
        self.resolved_at = datetime.utcnow()
