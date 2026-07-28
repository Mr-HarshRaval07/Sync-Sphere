from typing import Optional, List
from bson import ObjectId

from syncsphere.knowledge.domain.entities.document import KnowledgeDocument
from syncsphere.knowledge.domain.repositories.document_repository import KnowledgeDocumentRepository
from syncsphere.knowledge.infrastructure.documents.document_document import KnowledgeDocumentDocument
from syncsphere.knowledge.infrastructure.mappers import KnowledgeMappers

class MongoKnowledgeDocumentRepository(KnowledgeDocumentRepository):
    async def get_by_id(self, doc_id: str) -> Optional[KnowledgeDocument]:
        try:
            doc = await KnowledgeDocumentDocument.get(ObjectId(doc_id))
        except Exception:
            doc = await KnowledgeDocumentDocument.find_one(KnowledgeDocumentDocument.id == doc_id)
            
        if not doc:
            return None
        return KnowledgeMappers.document_to_domain(doc)

    async def list_by_source(self, source_id: str) -> List[KnowledgeDocument]:
        docs = await KnowledgeDocumentDocument.find(KnowledgeDocumentDocument.source_id == source_id).to_list()
        return [KnowledgeMappers.document_to_domain(d) for d in docs]

    async def list_by_org(self, org_id: str) -> List[KnowledgeDocument]:
        docs = await KnowledgeDocumentDocument.find(KnowledgeDocumentDocument.org_id == org_id).to_list()
        return [KnowledgeMappers.document_to_domain(d) for d in docs]

    async def save(self, document: KnowledgeDocument) -> None:
        doc = KnowledgeMappers.document_to_document_doc(document)
        doc.id = ObjectId(document.id) if document.id and len(document.id) == 24 else document.id
        
        existing = await KnowledgeDocumentDocument.find_one(KnowledgeDocumentDocument.id == doc.id)
        if existing:
            await existing.update({"$set": doc.model_dump(exclude={"id", "created_at"})})
        else:
            await doc.insert()

    async def delete(self, doc_id: str) -> None:
        try:
            doc = await KnowledgeDocumentDocument.get(ObjectId(doc_id))
        except Exception:
            doc = await KnowledgeDocumentDocument.find_one(KnowledgeDocumentDocument.id == doc_id)
            
        if doc:
            await doc.delete()
