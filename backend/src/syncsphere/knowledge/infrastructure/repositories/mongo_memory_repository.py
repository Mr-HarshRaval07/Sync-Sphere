from typing import Optional, Dict, Any
from syncsphere.knowledge.domain.repositories.memory_repository import MemoryRepository
from syncsphere.knowledge.infrastructure.documents.memory_document import MemoryDocument

class MongoMemoryRepository(MemoryRepository):
    async def get_memory(self, org_id: str, memory_type: str, resource_id: str) -> Optional[Dict[str, Any]]:
        doc = await MemoryDocument.find_one(
            MemoryDocument.org_id == org_id,
            MemoryDocument.memory_type == memory_type,
            MemoryDocument.resource_id == resource_id
        )
        if not doc:
            return None
        return doc.payload

    async def save_memory(self, org_id: str, memory_type: str, resource_id: str, payload: Dict[str, Any]) -> None:
        doc = await MemoryDocument.find_one(
            MemoryDocument.org_id == org_id,
            MemoryDocument.memory_type == memory_type,
            MemoryDocument.resource_id == resource_id
        )
        if doc:
            doc.payload = payload
            await doc.save()
        else:
            doc = MemoryDocument(
                org_id=org_id,
                memory_type=memory_type,
                resource_id=resource_id,
                payload=payload
            )
            await doc.insert()

    async def delete_memory(self, org_id: str, memory_type: str, resource_id: str) -> None:
        doc = await MemoryDocument.find_one(
            MemoryDocument.org_id == org_id,
            MemoryDocument.memory_type == memory_type,
            MemoryDocument.resource_id == resource_id
        )
        if doc:
            await doc.delete()
