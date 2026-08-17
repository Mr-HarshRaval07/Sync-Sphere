from abc import ABC, abstractmethod
from typing import Optional, List
from syncsphere.knowledge.domain.entities.cache_entry import SemanticCacheEntry

class SemanticCacheRepository(ABC):
    @abstractmethod
    async def get_by_id(self, cache_id: str) -> Optional[SemanticCacheEntry]:
        pass

    @abstractmethod
    async def list_by_org(self, org_id: str) -> List[SemanticCacheEntry]:
        pass

    @abstractmethod
    async def save(self, entry: SemanticCacheEntry) -> None:
        pass

    @abstractmethod
    async def delete(self, cache_id: str) -> None:
        pass

    @abstractmethod
    async def clear_by_org(self, org_id: str) -> None:
        pass
