from typing import List, Optional
from bson import ObjectId
from syncsphere.approval.domain.entities.approval_policy import ApprovalPolicy
from syncsphere.approval.domain.repositories import ApprovalPolicyRepository
from syncsphere.approval.infrastructure.documents.approval_policy_document import ApprovalPolicyDocument
from syncsphere.approval.infrastructure.mappers import ApprovalMapper

class MongoApprovalPolicyRepository(ApprovalPolicyRepository):
    async def get_by_id(self, policy_id: str) -> Optional[ApprovalPolicy]:
        try:
            doc = await ApprovalPolicyDocument.get(ObjectId(policy_id))
        except Exception:
            doc = await ApprovalPolicyDocument.find_one(ApprovalPolicyDocument.id == policy_id)
            
        if not doc:
            return None
        return ApprovalMapper.to_policy_entity(doc)

    async def list_by_org(self, org_id: str) -> List[ApprovalPolicy]:
        docs = await ApprovalPolicyDocument.find(ApprovalPolicyDocument.org_id == org_id).to_list()
        return [ApprovalMapper.to_policy_entity(d) for d in docs]

    async def save(self, policy: ApprovalPolicy) -> None:
        doc = ApprovalMapper.to_policy_document(policy)
        doc.id = ObjectId(policy.id) if len(policy.id) == 24 else policy.id
        
        existing = await ApprovalPolicyDocument.find_one(ApprovalPolicyDocument.id == doc.id)
        if existing:
            await existing.update({"$set": doc.model_dump(exclude={"id", "created_at"})})
        else:
            await doc.insert()

    async def delete(self, policy_id: str) -> None:
        try:
            doc = await ApprovalPolicyDocument.get(ObjectId(policy_id))
        except Exception:
            doc = await ApprovalPolicyDocument.find_one(ApprovalPolicyDocument.id == policy_id)
            
        if doc:
            await doc.delete()
