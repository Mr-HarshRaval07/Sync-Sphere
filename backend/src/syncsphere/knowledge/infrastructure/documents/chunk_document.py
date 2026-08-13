from pydantic import Field
from typing import List, Optional
from syncsphere.shared_kernel.infrastructure.mongodb.base_document import BaseTenantDocument

class KnowledgeChunkDocument(BaseTenantDocument):
    document_id: str
    source_id: str
    text: str
    token_count: int
    namespace: str
    embedding: List[float] = Field(default_factory=list)
    embedding_version_id: Optional[str] = None
    index_status: str

    class Settings:
        name = "knowledge_chunks"
        indexes = [
            "org_id",
            ("org_id", "document_id"),
            ("org_id", "source_id"),
            ("org_id", "namespace")
        ]
        # In a real MongoDB Atlas Vector Search environment, 
        # the vector search index is defined separately in Atlas UI/API.
