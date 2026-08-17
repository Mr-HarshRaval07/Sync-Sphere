from typing import Optional, List
from beanie import PydanticObjectId
from syncsphere.workflow.domain.repositories.workflow_template_repository import WorkflowTemplateRepository
from syncsphere.workflow.domain.entities.workflow_template import WorkflowTemplate
from syncsphere.workflow.infrastructure.documents.workflow_template_document import WorkflowTemplateDocument
from syncsphere.workflow.infrastructure.mappers import WorkflowMappers

class MongoWorkflowTemplateRepository(WorkflowTemplateRepository):
    """Concrete Mongo repository implementing WorkflowTemplateRepository using Beanie ODM."""

    async def save(self, template: WorkflowTemplate) -> None:
        doc = WorkflowMappers.template_to_document(template)
        if template.id:
            try:
                existing = await WorkflowTemplateDocument.get(PydanticObjectId(template.id))
                if existing:
                    existing.name = doc.name
                    existing.description = doc.description
                    existing.category = doc.category
                    existing.nodes = doc.nodes
                    existing.edges = doc.edges
                    existing.variables = doc.variables
                    await existing.save()
                    return
            except Exception:
                pass
        await doc.insert()
        template.id = str(doc.id)

    async def get_by_id(self, template_id: str) -> Optional[WorkflowTemplate]:
        try:
            doc = await WorkflowTemplateDocument.get(PydanticObjectId(template_id))
            return WorkflowMappers.template_to_domain(doc) if doc else None
        except Exception:
            return None

    async def list_templates(self, category: Optional[str] = None) -> List[WorkflowTemplate]:
        if category:
            docs = await WorkflowTemplateDocument.find(
                WorkflowTemplateDocument.category == category
            ).to_list()
        else:
            docs = await WorkflowTemplateDocument.find_all().to_list()
        return [WorkflowMappers.template_to_domain(doc) for doc in docs]
