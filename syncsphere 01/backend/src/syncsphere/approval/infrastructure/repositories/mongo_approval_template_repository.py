from typing import List, Optional
from bson import ObjectId
from syncsphere.approval.domain.entities.approval_template import ApprovalTemplate
from syncsphere.approval.domain.repositories import ApprovalTemplateRepository
from syncsphere.approval.infrastructure.documents.approval_template_document import ApprovalTemplateDocument
from syncsphere.approval.infrastructure.mappers import ApprovalMapper

class MongoApprovalTemplateRepository(ApprovalTemplateRepository):
    async def get_by_id(self, template_id: str) -> Optional[ApprovalTemplate]:
        try:
            doc = await ApprovalTemplateDocument.get(ObjectId(template_id))
        except Exception:
            doc = await ApprovalTemplateDocument.find_one(ApprovalTemplateDocument.id == template_id)
            
        if not doc:
            return None
        return ApprovalMapper.to_template_entity(doc)

    async def list_by_org(self, org_id: str) -> List[ApprovalTemplate]:
        docs = await ApprovalTemplateDocument.find(ApprovalTemplateDocument.org_id == org_id).to_list()
        return [ApprovalMapper.to_template_entity(d) for d in docs]

    async def save(self, template: ApprovalTemplate) -> None:
        doc = ApprovalMapper.to_template_document(template)
        doc.id = ObjectId(template.id) if len(template.id) == 24 else template.id
        
        existing = await ApprovalTemplateDocument.find_one(ApprovalTemplateDocument.id == doc.id)
        if existing:
            await existing.update({"$set": doc.model_dump(exclude={"id", "created_at"})})
        else:
            await doc.insert()

    async def delete(self, template_id: str) -> None:
        try:
            doc = await ApprovalTemplateDocument.get(ObjectId(template_id))
        except Exception:
            doc = await ApprovalTemplateDocument.find_one(ApprovalTemplateDocument.id == template_id)
            
        if doc:
            await doc.delete()
