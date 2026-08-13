from typing import List, Optional
from syncsphere.shared_kernel.domain.entity import Entity
from syncsphere.workflow.domain.value_objects import WorkflowGraph, Variable

class WorkflowTemplate(Entity):
    """
    WorkflowTemplate entity representing a pre-configured template blueprint
    for quick initialization of standard multi-agent workflows.
    """
    
    def __init__(
        self,
        name: str,
        description: str,
        graph: WorkflowGraph,
        variables: Optional[List[Variable]] = None,
        category: str = "general",
        id: Optional[str] = None,
        **kwargs
    ) -> None:
        super().__init__(id=id, **kwargs)
        self.name = name
        self.description = description
        self.graph = graph
        self.variables = variables or []
        self.category = category
