from typing import Optional
from datetime import datetime
from pydantic import Field
from syncsphere.shared_kernel.infrastructure.mongodb.base_document import BaseTenantDocument

class AlertDocument(BaseTenantDocument):
    name: str
    message: str
    severity: str = "WARNING"
    status: str = "ACTIVE"
    metric_name: Optional[str] = None
    resolved_at: Optional[datetime] = None

    class Settings:
        name = "observability_alerts"
        indexes = [
            "org_id",
            "status",
            "severity"
        ]
