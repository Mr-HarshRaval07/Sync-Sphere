from typing import List, Optional
from bson import ObjectId
from syncsphere.approval.domain.entities.approval_request import ApprovalRequest
from syncsphere.approval.domain.repositories import ApprovalRequestRepository
from syncsphere.approval.infrastructure.documents.approval_request_document import ApprovalRequestDocument
from syncsphere.approval.infrastructure.mappers import ApprovalMapper

class MongoApprovalRequestRepository(ApprovalRequestRepository):
    async def get_by_id(self, approval_id: str) -> Optional[ApprovalRequest]:
        print(f"--- [MongoApprovalRequestRepository] get_by_id called with: {approval_id}")
        try:
            doc = await ApprovalRequestDocument.get(ObjectId(approval_id))
            print(f"--- [MongoApprovalRequestRepository] get() returned: {doc is not None}")
        except Exception as e:
            print(f"--- [MongoApprovalRequestRepository] get() Exception: {e}")
            doc = await ApprovalRequestDocument.find_one(ApprovalRequestDocument.id == approval_id)
            print(f"--- [MongoApprovalRequestRepository] find_one() returned: {doc is not None}")
            
        if not doc:
            return None
        return ApprovalMapper.to_request_entity(doc)

    async def list_by_org(self, org_id: str) -> List[ApprovalRequest]:
        docs = await ApprovalRequestDocument.find(ApprovalRequestDocument.org_id == org_id).to_list()
        return [ApprovalMapper.to_request_entity(d) for d in docs]

    async def list_pending_by_user(self, org_id: str, user_id: str) -> List[ApprovalRequest]:
        # Finds active requests where current stage assignee contains user_id
        # In Beanie, we can filter using python expressions or mongo query
        # Since chain stages is nested, find all ACTIVE requests for org
        docs = await ApprovalRequestDocument.find(
            ApprovalRequestDocument.org_id == org_id,
            ApprovalRequestDocument.status == "ACTIVE"
        ).to_list()
        
        results = []
        for d in docs:
            stage = d.chain.stages[d.chain.current_stage_index]
            is_assigned = any(ass.user_id == user_id for ass in stage.assignments)
            if is_assigned:
                results.append(ApprovalMapper.to_request_entity(d))
                
        return results

    async def list_all_pending(self, org_id: str) -> List[ApprovalRequest]:
        docs = await ApprovalRequestDocument.find(
            ApprovalRequestDocument.org_id == org_id,
            ApprovalRequestDocument.status == "ACTIVE"
        ).to_list()
        return [ApprovalMapper.to_request_entity(d) for d in docs]

    async def save(self, request: ApprovalRequest) -> None:
        doc = ApprovalMapper.to_request_document(request)
        doc.id = ObjectId(request.id) if len(request.id) == 24 else request.id
        
        existing = await ApprovalRequestDocument.find_one(ApprovalRequestDocument.id == doc.id)
        if existing:
            await existing.update({"$set": doc.model_dump(exclude={"id", "created_at"})})
        else:
            await doc.insert()

    async def delete(self, approval_id: str) -> None:
        try:
            doc = await ApprovalRequestDocument.get(ObjectId(approval_id))
        except Exception:
            doc = await ApprovalRequestDocument.find_one(ApprovalRequestDocument.id == approval_id)
            
        if doc:
            await doc.delete()
