from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class VectorStore(ABC):
    """Abstract interface defining operations to query and store vector embeddings."""
    
    @abstractmethod
    async def add_vector(
        self,
        vector: List[float],
        metadata: Dict[str, Any],
        org_id: str,
        namespace: Optional[str] = None
    ) -> str:
        """Saves a vector with metadata inside a tenant partition namespace."""
        pass

    @abstractmethod
    async def similarity_search(
        self,
        query_vector: List[float],
        org_id: str,
        limit: int = 5,
        min_relevance: float = 0.7,
        namespace: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Returns top-K matching documents sorted by cosine similarity relevance."""
        pass
