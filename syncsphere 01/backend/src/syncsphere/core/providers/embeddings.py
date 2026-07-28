from abc import ABC, abstractmethod
from typing import List

class EmbeddingProvider(ABC):
    """Abstract interface defining the execution contract for text embedding generation."""
    
    @abstractmethod
    async def embed_query(self, text: str) -> List[float]:
        """Generates semantic float vector representation of a query string."""
        pass

    @abstractmethod
    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Generates semantic float vector representations of multiple document strings."""
        pass
