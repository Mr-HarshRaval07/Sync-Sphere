from typing import List, Optional
from syncsphere.shared_kernel.domain.entity import Entity
from syncsphere.workflow.domain.value_objects import WorkflowGraph, Variable

class WorkflowVersion(Entity):
    """
    WorkflowVersion entity representing a historical version snapshot of a Workflow.
    """
    
    def __init__(
        self,
        workflow_id: str,
        version: int,
        graph: WorkflowGraph,
        variables: Optional[List[Variable]] = None,
        description: Optional[str] = None,
        id: Optional[str] = None,
        **kwargs
    ) -> None:
        super().__init__(id=id, **kwargs)
        self.workflow_id = workflow_id
        self.version = version
        self.graph = graph
        self.variables = variables or []
        self.description = description or ""
