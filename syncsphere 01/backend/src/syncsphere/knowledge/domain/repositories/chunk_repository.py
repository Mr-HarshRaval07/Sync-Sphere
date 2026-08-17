from abc import ABC, abstractmethod
from typing import Optional, List
from syncsphere.knowledge.domain.entities.chunk import KnowledgeChunk

class KnowledgeChunkRepository(ABC):
    @abstractmethod
    async def get_by_id(self, chunk_id: str) -> Optional[KnowledgeChunk]:
        pass

    @abstractmethod
    async def list_by_document(self, doc_id: str) -> List[KnowledgeChunk]:
        pass

    @abstractmethod
    async def list_by_org(self, org_id: str) -> List[KnowledgeChunk]:
        pass

    @abstractmethod
    async def save(self, chunk: KnowledgeChunk) -> None:
        pass

    @abstractmethod
    async def delete(self, chunk_id: str) -> None:
        pass

    @abstractmethod
    async def delete_by_document(self, doc_id: str) -> None:
        pass

    @abstractmethod
    async def delete_by_source(self, source_id: str) -> None:
        pass
