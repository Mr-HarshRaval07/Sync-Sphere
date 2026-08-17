from pydantic import Field
from typing import List, Optional
from datetime import datetime
from syncsphere.shared_kernel.infrastructure.mongodb.base_document import BaseTenantDocument

class SemanticCacheEntryDocument(BaseTenantDocument):
    query_text: str
    response_text: str
    embedding: List[float] = Field(default_factory=list)
    similarity_threshold: float
    namespace: str
    eviction_policy: str
    hit_count: int
    last_accessed_at: datetime

    class Settings:
        name = "semantic_cache_entries"
        indexes = [
            "org_id",
            ("org_id", "namespace")
        ]
