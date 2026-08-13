from datetime import datetime
from typing import List, Optional
from syncsphere.shared_kernel.domain.entity import Entity

class SemanticCacheEntry(Entity):
    """
    SemanticCacheEntry acts as a vector-comparable query-response cache entry,
    allowing SyncSphere to reuse prompt generations semantically.
    """
    
    def __init__(
        self,
        org_id: str,
        query_text: str,
        response_text: str,
        embedding: List[float],
        similarity_threshold: float = 0.85,
        namespace: str = "default",
        eviction_policy: str = "LRU",  # LRU, LFU, FIFO
        hit_count: int = 0,
        last_accessed_at: Optional[datetime] = None,
        id: Optional[str] = None,
        **kwargs
    ) -> None:
        super().__init__(id=id, **kwargs)
        self.org_id = org_id
        self.query_text = query_text
        self.response_text = response_text
        self.embedding = embedding
        self.similarity_threshold = similarity_threshold
        self.namespace = namespace
        self.eviction_policy = eviction_policy
        self.hit_count = hit_count
        self.last_accessed_at = last_accessed_at or datetime.utcnow()

    def record_hit(self) -> None:
        self.hit_count += 1
        self.last_accessed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        
    def matches(self, target_embedding: List[float], similarity_fn) -> bool:
        """Determines if target vector meets the semantic similarity threshold."""
        score = similarity_fn(self.embedding, target_embedding)
        return score >= self.similarity_threshold
