from pydantic import Field
from typing import Dict, Any
from syncsphere.shared_kernel.infrastructure.mongodb.base_document import BaseTenantDocument

class MemoryDocument(BaseTenantDocument):
    memory_type: str  # conversation, planner, execution, workflow, org, user, etc.
    resource_id: str
    payload: Dict[str, Any] = Field(default_factory=dict)

    class Settings:
        name = "memory_entries"
        indexes = [
            "org_id",
            ("org_id", "memory_type"),
            ("org_id", "memory_type", "resource_id")
        ]
