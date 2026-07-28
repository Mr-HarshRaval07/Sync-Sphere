from typing import Optional, List
from bson import ObjectId

from syncsphere.knowledge.domain.entities.cache_entry import SemanticCacheEntry
from syncsphere.knowledge.domain.repositories import SemanticCacheRepository
from syncsphere.knowledge.infrastructure.documents.cache_document import SemanticCacheEntryDocument
from syncsphere.knowledge.infrastructure.mappers import KnowledgeMappers

class MongoSemanticCacheRepository(SemanticCacheRepository):
    async def get_by_id(self, cache_id: str) -> Optional[SemanticCacheEntry]:
        try:
            doc = await SemanticCacheEntryDocument.get(ObjectId(cache_id))
        except Exception:
            doc = await SemanticCacheEntryDocument.find_one(SemanticCacheEntryDocument.id == cache_id)
            
        if not doc:
            return None
        return KnowledgeMappers.cache_to_domain(doc)

    async def list_by_org(self, org_id: str) -> List[SemanticCacheEntry]:
        docs = await SemanticCacheEntryDocument.find(SemanticCacheEntryDocument.org_id == org_id).to_list()
        return [KnowledgeMappers.cache_to_domain(d) for d in docs]

    async def save(self, entry: SemanticCacheEntry) -> None:
        doc = KnowledgeMappers.cache_to_document(entry)
        doc.id = ObjectId(entry.id) if entry.id and len(entry.id) == 24 else entry.id
        
        existing = await SemanticCacheEntryDocument.find_one(SemanticCacheEntryDocument.id == doc.id)
        if existing:
            await existing.update({"$set": doc.model_dump(exclude={"id", "created_at"})})
        else:
            await doc.insert()

    async def delete(self, cache_id: str) -> None:
        try:
            doc = await SemanticCacheEntryDocument.get(ObjectId(cache_id))
        except Exception:
            doc = await SemanticCacheEntryDocument.find_one(SemanticCacheEntryDocument.id == cache_id)
            
        if doc:
            await doc.delete()

    async def clear_by_org(self, org_id: str) -> None:
        await SemanticCacheEntryDocument.find(SemanticCacheEntryDocument.org_id == org_id).delete()
