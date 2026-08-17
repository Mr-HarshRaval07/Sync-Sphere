from typing import Optional, Dict, Any
from datetime import datetime
from syncsphere.shared_kernel.domain.entity import Entity

class StructuredLog(Entity):
    def __init__(
        self,
        org_id: str,
        correlation_id: str,
        message: str,
        level: str = "INFO",
        module: str = "observability",
        timestamp: Optional[datetime] = None,
        context_info: Optional[Dict[str, Any]] = None,
        id: Optional[str] = None,
        **kwargs
    ) -> None:
        super().__init__(id=id, **kwargs)
        self.org_id = org_id
        self.correlation_id = correlation_id
        self.message = message
        self.level = level
        self.module = module
        self.timestamp = timestamp or datetime.utcnow()
        self.context_info = context_info or {}
