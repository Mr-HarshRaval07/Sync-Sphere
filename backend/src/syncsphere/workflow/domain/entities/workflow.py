from typing import List, Optional, Dict, Any
from syncsphere.shared_kernel.domain.aggregate_root import AggregateRoot
from syncsphere.workflow.domain.value_objects import (
    WorkflowStatus,
    WorkflowGraph,
    WorkflowNode,
    WorkflowEdge,
    Variable,
)
from syncsphere.workflow.domain.entities.workflow_version import WorkflowVersion

class Workflow(AggregateRoot):
    """
    Workflow aggregate root representing the core business blueprint in SyncSphere.
    Encapsulates the Directed Acyclic Graph (DAG) state, global variables, and versions.
    """
    
    def __init__(
        self,
        org_id: str,
        name: str,
        description: Optional[str] = "",
        status: WorkflowStatus = WorkflowStatus.DRAFT,
        graph: Optional[WorkflowGraph] = None,
        variables: Optional[List[Variable]] = None,
        active_version: Optional[int] = None,
        latest_version: int = 0,
        id: Optional[str] = None,
        **kwargs
    ) -> None:
        super().__init__(id=id, **kwargs)
        self.org_id = org_id
        self.name = name.strip()
        self.description = description
        self.status = status
        self.graph = graph or WorkflowGraph()
        self.variables = variables or []
        self.active_version = active_version
        self.latest_version = latest_version

    def add_node(self, node: WorkflowNode) -> None:
        """Adds a workflow step node to the draft graph."""
        self.graph.nodes[node.id] = node

    def remove_node(self, node_id: str) -> None:
        """Removes a workflow step node and any dangling connected edges."""
        self.graph.nodes.pop(node_id, None)
        self.graph.edges = [e for e in self.graph.edges if e.source_node_id != node_id and e.target_node_id != node_id]

    def add_edge(self, edge: WorkflowEdge) -> None:
        """Adds a directional execution dependency edge between nodes."""
        # Ensure nodes exist
        if edge.source_node_id in self.graph.nodes and edge.target_node_id in self.graph.nodes:
            # Check duplicate edge
            exists = any(
                e.source_node_id == edge.source_node_id and e.target_node_id == edge.target_node_id
                for e in self.graph.edges
            )
            if not exists:
                self.graph.edges.append(edge)

    def save_draft(self, version_description: Optional[str] = None) -> WorkflowVersion:
        """Creates a snapshot version of the current graph as a DRAFT."""
        self.latest_version += 1
        self.active_version = self.latest_version
        
        snapshot_graph = self.graph.model_copy(deep=True)
        snapshot_vars = [v.model_copy(deep=True) for v in self.variables]
        
        return WorkflowVersion(
            org_id=self.org_id,
            workflow_id=self.id,
            version=self.active_version,
            graph=snapshot_graph,
            variables=snapshot_vars,
            description=version_description or f"Draft version {self.active_version}",
            state="DRAFT"
        )

    def publish(self, version_description: Optional[str] = None) -> WorkflowVersion:
        """
        Creates a new immutable version snapshot from the current graph state.
        Transitions status to PUBLISHED and increments active version numbers.
        """
        self.latest_version += 1
        self.active_version = self.latest_version
        self.status = WorkflowStatus.PUBLISHED
        
        # Snapshot current variables and graph state
        snapshot_graph = self.graph.model_copy(deep=True)
        snapshot_vars = [v.model_copy(deep=True) for v in self.variables]
        
        return WorkflowVersion(
            org_id=self.org_id,
            workflow_id=self.id,
            version=self.active_version,
            graph=snapshot_graph,
            variables=snapshot_vars,
            description=version_description or f"Snapshot version {self.active_version}",
            state="PUBLISHED"
        )

    def archive(self) -> None:
        """Archives the workflow, blocking future automated planner orchestrations."""
        self.status = WorkflowStatus.ARCHIVED

    def clone(self, new_name: str) -> "Workflow":
        """Generates a deep copy draft of the workflow resetting history."""
        cloned_graph = self.graph.model_copy(deep=True)
        cloned_vars = [v.model_copy(deep=True) for v in self.variables]
        
        return Workflow(
            org_id=self.org_id,
            name=new_name,
            description=f"Cloned copy of '{self.name}'. {self.description}",
            status=WorkflowStatus.DRAFT,
            graph=cloned_graph,
            variables=cloned_vars,
            active_version=None,
            latest_version=0
        )
