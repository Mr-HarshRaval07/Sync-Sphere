from typing import Optional, List
from syncsphere.shared_kernel.domain.entity import Entity

class KnowledgeChunk(Entity):
    """
    KnowledgeChunk represents a raw segment of text extracted from a parent document.
    It contains token size metrics, corresponding vector floats, and embedding model versions.
    """
    
    def __init__(
        self,
        document_id: str,
        source_id: str,
        org_id: str,
        text: str,
        token_count: int,
        namespace: str = "default",
        embedding: Optional[List[float]] = None,
        embedding_version_id: Optional[str] = None,
        index_status: str = "pending",  # pending, indexed, failed
        id: Optional[str] = None,
        **kwargs
    ) -> None:
        super().__init__(id=id, **kwargs)
        self.document_id = document_id
        self.source_id = source_id
        self.org_id = org_id
        self.text = text
        self.token_count = token_count
        self.namespace = namespace
        self.embedding = embedding or []
        self.embedding_version_id = embedding_version_id
        self.index_status = index_status
