from pydantic import Field
from typing import List, Dict, Any, Optional
from syncsphere.shared_kernel.infrastructure.mongodb.base_document import BaseTenantDocument

class KnowledgeDocumentDocument(BaseTenantDocument):
    source_id: str
    title: str
    content: str
    namespace: str
    status: str
    version: int
    metadata: Dict[str, Any] = Field(default_factory=dict)
    relationships: List[Dict[str, Any]] = Field(default_factory=list)

    class Settings:
        name = "knowledge_documents"
        indexes = [
            "org_id",
            ("org_id", "source_id"),
            ("org_id", "namespace")
        ]
