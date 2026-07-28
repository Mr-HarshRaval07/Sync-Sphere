from typing import Optional, List
from beanie import PydanticObjectId
from syncsphere.workflow.domain.repositories.workflow_repository import WorkflowRepository
from syncsphere.workflow.domain.entities.workflow import Workflow
from syncsphere.workflow.infrastructure.documents.workflow_document import WorkflowDocument
from syncsphere.workflow.infrastructure.mappers import WorkflowMappers

class MongoWorkflowRepository(WorkflowRepository):
    """Concrete Mongo repository implementing WorkflowRepository using Beanie ODM."""

    async def save(self, workflow: Workflow) -> None:
        doc = WorkflowMappers.workflow_to_document(workflow)
        if workflow.id:
            try:
                existing_doc = await WorkflowDocument.get(PydanticObjectId(workflow.id))
                if existing_doc:
                    existing_doc.name = doc.name
                    existing_doc.description = doc.description
                    existing_doc.status = doc.status
                    existing_doc.nodes = doc.nodes
                    existing_doc.edges = doc.edges
                    existing_doc.variables = doc.variables
                    existing_doc.active_version = doc.active_version
                    existing_doc.latest_version = doc.latest_version
                    await existing_doc.save()
                    return
            except Exception:
                pass
        await doc.insert()
        workflow.id = str(doc.id)

    async def get_by_id(self, workflow_id: str) -> Optional[Workflow]:
        try:
            doc = await WorkflowDocument.get(PydanticObjectId(workflow_id))
            return WorkflowMappers.workflow_to_domain(doc) if doc else None
        except Exception:
            return None

    async def get_by_name(self, org_id: str, name: str) -> Optional[Workflow]:
        doc = await WorkflowDocument.find_one(
            WorkflowDocument.org_id == org_id,
            WorkflowDocument.name == name.strip()
        )
        return WorkflowMappers.workflow_to_domain(doc) if doc else None

    async def list_by_org(self, org_id: str, page: int, page_size: int) -> List[Workflow]:
        skip = (page - 1) * page_size
        docs = await WorkflowDocument.find(
            WorkflowDocument.org_id == org_id,
            WorkflowDocument.status != "ARCHIVED"
        ).skip(skip).limit(page_size).to_list()
        return [WorkflowMappers.workflow_to_domain(doc) for doc in docs]

    async def count_by_org(self, org_id: str) -> int:
        return await WorkflowDocument.find(
            WorkflowDocument.org_id == org_id,
            WorkflowDocument.status != "ARCHIVED"
        ).count()

    async def delete(self, workflow_id: str) -> None:
        try:
            doc = await WorkflowDocument.get(PydanticObjectId(workflow_id))
            if doc:
                await doc.delete()
        except Exception:
            pass
