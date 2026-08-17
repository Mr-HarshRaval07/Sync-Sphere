from typing import Optional, List
from bson import ObjectId

from syncsphere.knowledge.domain.entities.source import KnowledgeSource
from syncsphere.knowledge.domain.repositories.source_repository import KnowledgeSourceRepository
from syncsphere.knowledge.infrastructure.documents.source_document import KnowledgeSourceDocument
from syncsphere.knowledge.infrastructure.mappers import KnowledgeMappers

class MongoKnowledgeSourceRepository(KnowledgeSourceRepository):
    async def get_by_id(self, source_id: str) -> Optional[KnowledgeSource]:
        try:
            doc = await KnowledgeSourceDocument.get(ObjectId(source_id))
        except Exception:
            doc = await KnowledgeSourceDocument.find_one(KnowledgeSourceDocument.id == source_id)
            
        if not doc:
            return None
        return KnowledgeMappers.source_to_domain(doc)

    async def list_by_org(self, org_id: str) -> List[KnowledgeSource]:
        docs = await KnowledgeSourceDocument.find(KnowledgeSourceDocument.org_id == org_id).to_list()
        return [KnowledgeMappers.source_to_domain(d) for d in docs]

    async def save(self, source: KnowledgeSource) -> None:
        doc = KnowledgeMappers.source_to_document(source)
        doc.id = ObjectId(source.id) if source.id and len(source.id) == 24 else source.id
        
        # Upsert logic
        existing = await KnowledgeSourceDocument.find_one(KnowledgeSourceDocument.id == doc.id)
        if existing:
            await existing.update({"$set": doc.model_dump(exclude={"id", "created_at"})})
        else:
            await doc.insert()

    async def delete(self, source_id: str) -> None:
        try:
            doc = await KnowledgeSourceDocument.get(ObjectId(source_id))
        except Exception:
            doc = await KnowledgeSourceDocument.find_one(KnowledgeSourceDocument.id == source_id)
            
        if doc:
            await doc.delete()
