import logging
from typing import Dict, Any, List, Optional
from syncsphere.shared_kernel.types.result import Result
from syncsphere.shared_kernel.domain.domain_exception import EntityNotFoundException, ValidationException
from syncsphere.workflow.domain.entities.workflow import Workflow
from syncsphere.workflow.domain.entities.workflow_version import WorkflowVersion
from syncsphere.workflow.domain.value_objects import (
    WorkflowStatus,
    WorkflowGraph,
    WorkflowNode,
    WorkflowEdge,
    Variable,
    ExecutionPlan
)
from syncsphere.workflow.domain.repositories import WorkflowRepository, WorkflowVersionRepository
from syncsphere.workflow.infrastructure.dag.compiler import WorkflowCompiler
from syncsphere.workflow.infrastructure.dag.validator import DAGValidator

logger = logging.getLogger("syncsphere.workflow.application.services.workflow_service")

class WorkflowApplicationService:
    """Application Service coordinating Workflow lifecycle management and graph compilations."""

    def __init__(
        self,
        workflow_repo: WorkflowRepository,
        version_repo: WorkflowVersionRepository
    ) -> None:
        self.workflow_repo = workflow_repo
        self.version_repo = version_repo

    async def create_workflow(
        self,
        org_id: str,
        name: str,
        description: Optional[str] = "",
        variables: Optional[List[Variable]] = None
    ) -> Result[Workflow, Exception]:
        """Creates a new workflow configuration draft."""
        logger.info("Creating workflow: %s in org_id: %s", name, org_id)
        
        # Check duplicate name in org context
        existing = await self.workflow_repo.get_by_name(org_id, name)
        if existing and existing.status != "ARCHIVED":
            return Result.fail(ValidationException(
                code="DUPLICATE_WORKFLOW_NAME",
                message=f"Workflow with name '{name}' already exists in your organization."
            ))

        workflow = Workflow(
            org_id=org_id,
            name=name,
            description=description,
            variables=variables
        )
        await self.workflow_repo.save(workflow)
        return Result.ok(workflow)

    async def update_workflow(
        self,
        org_id: str,
        workflow_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        nodes: Optional[Dict[str, WorkflowNode]] = None,
        edges: Optional[List[WorkflowEdge]] = None,
        variables: Optional[List[Variable]] = None
    ) -> Result[Workflow, Exception]:
        """Updates the details, steps, and edges of a draft workflow."""
        workflow = await self.workflow_repo.get_by_id(workflow_id)
        if not workflow or workflow.org_id != org_id:
            return Result.fail(EntityNotFoundException("WORKFLOW_NOT_FOUND", "Workflow not found."))

        if workflow.status == WorkflowStatus.ARCHIVED:
            return Result.fail(ValidationException("WORKFLOW_ARCHIVED", "Cannot edit an archived workflow."))

        # Update metadata
        if name is not None:
            workflow.name = name
        if description is not None:
            workflow.description = description
            
        # Update graph structure
        if nodes is not None:
            workflow.graph.nodes = nodes
        if edges is not None:
            workflow.graph.edges = edges
        if variables is not None:
            workflow.variables = variables

        # Reset to DRAFT when modified
        workflow.status = WorkflowStatus.DRAFT

        # 1. Create a draft version snapshot
        draft_version = workflow.save_draft(version_description="Draft saved automatically")
        
        # 2. Persist updated aggregate and new version
        await self.version_repo.save(draft_version)
        await self.workflow_repo.save(workflow)
        return Result.ok(workflow)

    async def clone_workflow(
        self,
        org_id: str,
        workflow_id: str,
        new_name: str
    ) -> Result[Workflow, Exception]:
        """Generates a deep copy draft of an existing workflow graph."""
        workflow = await self.workflow_repo.get_by_id(workflow_id)
        if not workflow or workflow.org_id != org_id:
            return Result.fail(EntityNotFoundException("WORKFLOW_NOT_FOUND", "Workflow not found."))

        cloned = workflow.clone(new_name=new_name)
        await self.workflow_repo.save(cloned)
        return Result.ok(cloned)

    async def publish_workflow(
        self,
        org_id: str,
        workflow_id: str,
        version_description: Optional[str] = None
    ) -> Result[WorkflowVersion, Exception]:
        """Validates graph correctness and publishes a snapshot version."""
        workflow = await self.workflow_repo.get_by_id(workflow_id)
        if not workflow or workflow.org_id != org_id:
            return Result.fail(EntityNotFoundException("WORKFLOW_NOT_FOUND", "Workflow not found."))

        # 1. Compile to validate DAG structural constraints
        try:
            WorkflowCompiler.compile(workflow)
        except Exception as e:
            return Result.fail(e)

        # 2. Publish and get snapshot entity
        version_snapshot = workflow.publish(version_description)

        # 3. Persist updated aggregate and new version
        await self.workflow_repo.save(workflow)
        await self.version_repo.save(version_snapshot)

        return Result.ok(version_snapshot)

    async def compile_workflow(
        self,
        org_id: str,
        workflow_id: str
    ) -> Result[ExecutionPlan, Exception]:
        """Compiles workflow steps topologically into an ExecutionPlan."""
        workflow = await self.workflow_repo.get_by_id(workflow_id)
        if not workflow or workflow.org_id != org_id:
            return Result.fail(EntityNotFoundException("WORKFLOW_NOT_FOUND", "Workflow not found."))

        try:
            plan = WorkflowCompiler.compile(workflow)
            return Result.ok(plan)
        except Exception as e:
            return Result.fail(e)

    async def archive_workflow(self, org_id: str, workflow_id: str) -> Result[bool, Exception]:
        """Archives the workflow."""
        workflow = await self.workflow_repo.get_by_id(workflow_id)
        if not workflow or workflow.org_id != org_id:
            return Result.fail(EntityNotFoundException("WORKFLOW_NOT_FOUND", "Workflow not found."))

        workflow.archive()
        await self.workflow_repo.save(workflow)
        return Result.ok(True)
