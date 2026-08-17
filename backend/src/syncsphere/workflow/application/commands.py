from pydantic import Field
from typing import Dict, Any, List, Optional
from syncsphere.shared_kernel.types.contracts import BaseCommand
from syncsphere.workflow.domain.value_objects import WorkflowNode, WorkflowEdge, Variable

class CreateWorkflowCommand(BaseCommand):
    """Command to create a new workflow config."""
    name: str
    description: Optional[str] = ""
    variables: List[Variable] = Field(default_factory=list)


class UpdateWorkflowCommand(BaseCommand):
    """Command to update workflow graph structure and details."""
    workflow_id: str
    name: Optional[str] = None
    description: Optional[str] = None
    nodes: Optional[Dict[str, WorkflowNode]] = None
    edges: Optional[List[WorkflowEdge]] = None
    variables: Optional[List[Variable]] = None


class CloneWorkflowCommand(BaseCommand):
    """Command to clone a workflow blueprint."""
    workflow_id: str
    new_name: str


class PublishWorkflowCommand(BaseCommand):
    """Command to publish a workflow snapshot and increment versions."""
    workflow_id: str
    version_description: Optional[str] = None


class ArchiveWorkflowCommand(BaseCommand):
    """Command to archive a workflow."""
    workflow_id: str


class ImportWorkflowCommand(BaseCommand):
    """Command to import a workflow from a raw JSON serialization structure."""
    name: str
    description: Optional[str] = ""
    nodes: Dict[str, WorkflowNode] = Field(default_factory=dict)
    edges: List[WorkflowEdge] = Field(default_factory=list)
    variables: List[Variable] = Field(default_factory=list)
