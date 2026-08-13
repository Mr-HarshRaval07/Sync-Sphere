from syncsphere.workflow.domain.entities.workflow import Workflow
from syncsphere.workflow.domain.entities.workflow_version import WorkflowVersion
from syncsphere.workflow.domain.entities.workflow_template import WorkflowTemplate
from syncsphere.workflow.domain.value_objects import WorkflowGraph, Variable
from syncsphere.workflow.infrastructure.documents import (
    WorkflowDocument,
    WorkflowVersionDocument,
    WorkflowTemplateDocument
)

class WorkflowMappers:
    """Utility conversions between Workflow Domain models and Beanie Documents."""

    @staticmethod
    def workflow_to_domain(doc: WorkflowDocument) -> Workflow:
        variables = [Variable(**v) for v in doc.variables]
        graph = WorkflowGraph(nodes=doc.nodes, edges=doc.edges)
        return Workflow(
            org_id=doc.org_id,
            name=doc.name,
            description=doc.description,
            status=doc.status,
            graph=graph,
            variables=variables,
            active_version=doc.active_version,
            latest_version=doc.latest_version,
            id=str(doc.id),
            created_at=doc.created_at,
            updated_at=doc.updated_at
        )

    @staticmethod
    def workflow_to_document(domain: Workflow) -> WorkflowDocument:
        variables = [v.model_dump() for v in domain.variables]
        return WorkflowDocument(
            org_id=domain.org_id,
            name=domain.name,
            description=domain.description,
            status=domain.status,
            nodes=domain.graph.nodes,
            edges=domain.graph.edges,
            variables=variables,
            active_version=domain.active_version,
            latest_version=domain.latest_version,
            created_at=domain.created_at,
            updated_at=domain.updated_at
        )

    @staticmethod
    def version_to_domain(doc: WorkflowVersionDocument) -> WorkflowVersion:
        variables = [Variable(**v) for v in doc.variables]
        graph = WorkflowGraph(nodes=doc.nodes, edges=doc.edges)
        return WorkflowVersion(
            org_id=doc.org_id,
            workflow_id=doc.workflow_id,
            version=doc.version,
            graph=graph,
            variables=variables,
            description=doc.description,
            state=doc.state,
            id=str(doc.id),
            created_at=doc.created_at,
            updated_at=doc.updated_at
        )

    @staticmethod
    def version_to_document(domain: WorkflowVersion) -> WorkflowVersionDocument:
        variables = [v.model_dump() for v in domain.variables]
        return WorkflowVersionDocument(
            org_id=domain.org_id or "",
            workflow_id=domain.workflow_id,
            version=domain.version,
            description=domain.description,
            state=domain.state,
            nodes=domain.graph.nodes,
            edges=domain.graph.edges,
            variables=variables,
            created_at=domain.created_at,
            updated_at=domain.updated_at
        )

    @staticmethod
    def template_to_domain(doc: WorkflowTemplateDocument) -> WorkflowTemplate:
        variables = [Variable(**v) for v in doc.variables]
        graph = WorkflowGraph(nodes=doc.nodes, edges=doc.edges)
        return WorkflowTemplate(
            name=doc.name,
            description=doc.description,
            graph=graph,
            variables=variables,
            category=doc.category,
            id=str(doc.id),
            created_at=doc.created_at,
            updated_at=doc.updated_at
        )

    @staticmethod
    def template_to_document(domain: WorkflowTemplate) -> WorkflowTemplateDocument:
        variables = [v.model_dump() for v in domain.variables]
        return WorkflowTemplateDocument(
            name=domain.name,
            description=domain.description,
            category=domain.category,
            nodes=domain.graph.nodes,
            edges=domain.graph.edges,
            variables=variables,
            created_at=domain.created_at,
            updated_at=domain.updated_at
        )
