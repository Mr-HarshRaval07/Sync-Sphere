from typing import Optional, List
from bson import ObjectId

from syncsphere.knowledge.domain.entities.chunk import KnowledgeChunk
from syncsphere.knowledge.domain.repositories.chunk_repository import KnowledgeChunkRepository
from syncsphere.knowledge.infrastructure.documents.chunk_document import KnowledgeChunkDocument
from syncsphere.knowledge.infrastructure.mappers import KnowledgeMappers

class MongoKnowledgeChunkRepository(KnowledgeChunkRepository):
    async def get_by_id(self, chunk_id: str) -> Optional[KnowledgeChunk]:
        try:
            doc = await KnowledgeChunkDocument.get(ObjectId(chunk_id))
        except Exception:
            doc = await KnowledgeChunkDocument.find_one(KnowledgeChunkDocument.id == chunk_id)
            
        if not doc:
            return None
        return KnowledgeMappers.chunk_to_domain(doc)

    async def list_by_document(self, doc_id: str) -> List[KnowledgeChunk]:
        docs = await KnowledgeChunkDocument.find(KnowledgeChunkDocument.document_id == doc_id).to_list()
        return [KnowledgeMappers.chunk_to_domain(d) for d in docs]

    async def list_by_org(self, org_id: str) -> List[KnowledgeChunk]:
        docs = await KnowledgeChunkDocument.find(KnowledgeChunkDocument.org_id == org_id).to_list()
        return [KnowledgeMappers.chunk_to_domain(d) for d in docs]

    async def save(self, chunk: KnowledgeChunk) -> None:
        doc = KnowledgeMappers.chunk_to_document(chunk)
        doc.id = ObjectId(chunk.id) if chunk.id and len(chunk.id) == 24 else chunk.id
        
        existing = await KnowledgeChunkDocument.find_one(KnowledgeChunkDocument.id == doc.id)
        if existing:
            await existing.update({"$set": doc.model_dump(exclude={"id", "created_at"})})
        else:
            await doc.insert()

    async def delete(self, chunk_id: str) -> None:
        try:
            doc = await KnowledgeChunkDocument.get(ObjectId(chunk_id))
        except Exception:
            doc = await KnowledgeChunkDocument.find_one(KnowledgeChunkDocument.id == chunk_id)
            
        if doc:
            await doc.delete()

    async def delete_by_document(self, doc_id: str) -> None:
        await KnowledgeChunkDocument.find(KnowledgeChunkDocument.document_id == doc_id).delete()

    async def delete_by_source(self, source_id: str) -> None:
        await KnowledgeChunkDocument.find(KnowledgeChunkDocument.source_id == source_id).delete()
