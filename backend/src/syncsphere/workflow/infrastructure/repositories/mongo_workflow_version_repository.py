from typing import Optional, List
from beanie import PydanticObjectId
from syncsphere.workflow.domain.repositories.workflow_version_repository import WorkflowVersionRepository
from syncsphere.workflow.domain.entities.workflow_version import WorkflowVersion
from syncsphere.workflow.infrastructure.documents.workflow_version_document import WorkflowVersionDocument
from syncsphere.workflow.infrastructure.mappers import WorkflowMappers

class MongoWorkflowVersionRepository(WorkflowVersionRepository):
    """Concrete Mongo repository implementing WorkflowVersionRepository using Beanie ODM."""

    async def save(self, version: WorkflowVersion) -> None:
        doc = WorkflowMappers.version_to_document(version)
        if version.id:
            try:
                existing = await WorkflowVersionDocument.get(PydanticObjectId(version.id))
                if existing:
                    existing.description = doc.description
                    existing.nodes = doc.nodes
                    existing.edges = doc.edges
                    existing.variables = doc.variables
                    await existing.save()
                    return
            except Exception:
                pass
        await doc.insert()
        version.id = str(doc.id)

    async def get_by_version(self, workflow_id: str, version: int) -> Optional[WorkflowVersion]:
        doc = await WorkflowVersionDocument.find_one(
            WorkflowVersionDocument.workflow_id == workflow_id,
            WorkflowVersionDocument.version == version
        )
        return WorkflowMappers.version_to_domain(doc) if doc else None

    async def list_versions(self, workflow_id: str) -> List[WorkflowVersion]:
        docs = await WorkflowVersionDocument.find(
            WorkflowVersionDocument.workflow_id == workflow_id
        ).to_list()
        return [WorkflowMappers.version_to_domain(doc) for doc in docs]
