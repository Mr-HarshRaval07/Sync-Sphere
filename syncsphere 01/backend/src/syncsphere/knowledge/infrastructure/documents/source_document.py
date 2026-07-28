from pydantic import Field
from typing import Dict, Any, Optional
from datetime import datetime
from syncsphere.shared_kernel.infrastructure.mongodb.base_document import BaseTenantDocument

class KnowledgeSourceDocument(BaseTenantDocument):
    name: str
    type: str
    config: Dict[str, Any] = Field(default_factory=dict)
    policy: Dict[str, Any] = Field(default_factory=dict)
    sync_strategy: str
    sync_schedule: Optional[str] = None
    status: str
    last_sync_at: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Settings:
        name = "knowledge_sources"
        indexes = [
            "org_id",
            ("org_id", "type"),
            ("org_id", "status")
        ]
