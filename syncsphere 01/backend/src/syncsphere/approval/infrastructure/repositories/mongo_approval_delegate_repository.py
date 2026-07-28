from typing import List, Optional
from bson import ObjectId
from syncsphere.approval.domain.entities.approval_delegate import ApprovalDelegate
from syncsphere.approval.domain.repositories import ApprovalDelegateRepository
from syncsphere.approval.infrastructure.documents.approval_delegate_document import ApprovalDelegateDocument
from syncsphere.approval.infrastructure.mappers import ApprovalMapper

class MongoApprovalDelegateRepository(ApprovalDelegateRepository):
    async def get_by_id(self, delegate_id: str) -> Optional[ApprovalDelegate]:
        try:
            doc = await ApprovalDelegateDocument.get(ObjectId(delegate_id))
        except Exception:
            doc = await ApprovalDelegateDocument.find_one(ApprovalDelegateDocument.id == delegate_id)
            
        if not doc:
            return None
        return ApprovalMapper.to_delegate_entity(doc)

    async def list_by_org(self, org_id: str) -> List[ApprovalDelegate]:
        docs = await ApprovalDelegateDocument.find(ApprovalDelegateDocument.org_id == org_id).to_list()
        return [ApprovalMapper.to_delegate_entity(d) for d in docs]

    async def list_active_delegates_for_user(self, org_id: str, user_id: str) -> List[ApprovalDelegate]:
        docs = await ApprovalDelegateDocument.find(
            ApprovalDelegateDocument.org_id == org_id,
            ApprovalDelegateDocument.from_user_id == user_id,
            ApprovalDelegateDocument.is_active == True
        ).to_list()
        return [ApprovalMapper.to_delegate_entity(d) for d in docs]

    async def save(self, delegate: ApprovalDelegate) -> None:
        doc = ApprovalMapper.to_delegate_document(delegate)
        doc.id = ObjectId(delegate.id) if len(delegate.id) == 24 else delegate.id
        
        existing = await ApprovalDelegateDocument.find_one(ApprovalDelegateDocument.id == doc.id)
        if existing:
            await existing.update({"$set": doc.model_dump(exclude={"id", "created_at"})})
        else:
            await doc.insert()

    async def delete(self, delegate_id: str) -> None:
        try:
            doc = await ApprovalDelegateDocument.get(ObjectId(delegate_id))
        except Exception:
            doc = await ApprovalDelegateDocument.find_one(ApprovalDelegateDocument.id == delegate_id)
            
        if doc:
            await doc.delete()
