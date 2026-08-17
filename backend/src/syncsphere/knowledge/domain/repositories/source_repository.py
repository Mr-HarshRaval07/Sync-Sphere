from abc import ABC, abstractmethod
from typing import Optional, List
from syncsphere.knowledge.domain.entities.source import KnowledgeSource

class KnowledgeSourceRepository(ABC):
    @abstractmethod
    async def get_by_id(self, source_id: str) -> Optional[KnowledgeSource]:
        pass

    @abstractmethod
    async def list_by_org(self, org_id: str) -> List[KnowledgeSource]:
        pass

    @abstractmethod
    async def save(self, source: KnowledgeSource) -> None:
        pass

    @abstractmethod
    async def delete(self, source_id: str) -> None:
        pass
