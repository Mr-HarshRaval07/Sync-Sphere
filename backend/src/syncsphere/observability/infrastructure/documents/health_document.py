from typing import List
from pydantic import Field
from syncsphere.shared_kernel.infrastructure.mongodb.base_document import BaseTenantDocument
from syncsphere.observability.domain.value_objects import ServiceStatus

class HealthCheckDocument(BaseTenantDocument):
    services: List[ServiceStatus] = Field(default_factory=list)

    class Settings:
        name = "observability_health_checks"
        indexes = [
            "org_id",
            "created_at"
        ]
