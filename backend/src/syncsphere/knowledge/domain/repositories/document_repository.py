from abc import ABC, abstractmethod
from typing import Optional, List
from syncsphere.knowledge.domain.entities.document import KnowledgeDocument

class KnowledgeDocumentRepository(ABC):
    @abstractmethod
    async def get_by_id(self, doc_id: str) -> Optional[KnowledgeDocument]:
        pass

    @abstractmethod
    async def list_by_source(self, source_id: str) -> List[KnowledgeDocument]:
        pass

    @abstractmethod
    async def list_by_org(self, org_id: str) -> List[KnowledgeDocument]:
        pass

    @abstractmethod
    async def save(self, document: KnowledgeDocument) -> None:
        pass

    @abstractmethod
    async def delete(self, doc_id: str) -> None:
        pass
