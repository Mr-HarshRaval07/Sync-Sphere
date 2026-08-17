import re
import logging
from typing import Dict, Any, List, Set
from syncsphere.workflow.domain.value_objects import WorkflowGraph, WorkflowNode, WorkflowEdge
from syncsphere.workflow.domain.exceptions import InvalidWorkflowGraphException

logger = logging.getLogger("syncsphere.workflow.infrastructure.dag.validator")

class CycleDetector:
    """Detects cycles in a Directed Acyclic Graph (DAG) using DFS coloring (white/gray/black)."""

    @staticmethod
    def has_cycle(graph: WorkflowGraph) -> bool:
        # Build adjacency list
        adj: Dict[str, List[str]] = {nid: [] for nid in graph.nodes}
        for edge in graph.edges:
            # If source or target node doesn't exist, ignore (handled in general validation)
            if edge.source_node_id in adj and edge.target_node_id in adj:
                adj[edge.source_node_id].append(edge.target_node_id)

        # Visited status: 0=unvisited (white), 1=visiting (gray), 2=visited (black)
        state: Dict[str, int] = {nid: 0 for nid in graph.nodes}

        def dfs(node_id: str) -> bool:
            state[node_id] = 1 # Mark gray
            for neighbor in adj[node_id]:
                if state[neighbor] == 1:
                    return True # Cycle detected
                elif state[neighbor] == 0:
                    if dfs(neighbor):
                        return True
            state[node_id] = 2 # Mark black
            return False

        for nid in graph.nodes:
            if state[nid] == 0:
                if dfs(nid):
                    return True
        return False


class DAGValidator:
    """Validates full structural and semantic correctness of a WorkflowGraph."""

    @staticmethod
    def validate(graph: WorkflowGraph, variables: List[Any] = None) -> None:
        """
        Validates graph structure, cycles, variable bindings, and connections.
        Raises InvalidWorkflowGraphException on failure.
        """
        if not graph.nodes:
            raise InvalidWorkflowGraphException("Workflow must contain at least one step node.")

        # 1. Validate edge references
        for edge in graph.edges:
            if edge.source_node_id not in graph.nodes:
                raise InvalidWorkflowGraphException(
                    f"Edge source node '{edge.source_node_id}' does not exist in workflow."
                )
            if edge.target_node_id not in graph.nodes:
                raise InvalidWorkflowGraphException(
                    f"Edge target node '{edge.target_node_id}' does not exist in workflow."
                )

        # 2. Cycle Detection
        if CycleDetector.has_cycle(graph):
            raise InvalidWorkflowGraphException(
                "Cycle detected in workflow graph. SyncSphere workflows must be Directed Acyclic Graphs (DAG)."
            )

        # 3. Validate variables and bindings
        # We parse bindings to check if they refer to valid upstream nodes
        valid_variables = {v.name for v in (variables or [])}
        
        # Build topological sort to determine causal direction
        try:
            topo_order = DAGValidator.topological_sort(graph)
        except Exception:
            raise InvalidWorkflowGraphException("Failed to topologically sort the workflow graph.")

        node_positions = {nid: idx for idx, nid in enumerate(topo_order)}

        for nid, node in graph.nodes.items():
            # Validate input bindings refer ONLY to upstream nodes
            for binding in node.input_bindings:
                if binding.source_node_id not in graph.nodes:
                    raise InvalidWorkflowGraphException(
                        f"Input binding for node '{nid}' references non-existent node '{binding.source_node_id}'"
                    )
                # Anti-causality check: source must be upstream in topological order
                if node_positions[binding.source_node_id] >= node_positions[nid]:
                    raise InvalidWorkflowGraphException(
                        f"Input binding for node '{nid}' references downstream/same node '{binding.source_node_id}'"
                    )

    @staticmethod
    def topological_sort(graph: WorkflowGraph) -> List[str]:
        """Performs topological sort using Kahn's algorithm."""
        in_degree = {nid: 0 for nid in graph.nodes}
        adj = {nid: [] for nid in graph.nodes}

        for edge in graph.edges:
            if edge.source_node_id in adj and edge.target_node_id in adj:
                adj[edge.source_node_id].append(edge.target_node_id)
                in_degree[edge.target_node_id] += 1

        queue = [nid for nid in graph.nodes if in_degree[nid] == 0]
        order = []

        while queue:
            node = queue.pop(0)
            order.append(node)
            for neighbor in adj[node]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if len(order) != len(graph.nodes):
            raise InvalidWorkflowGraphException("Cyclic graph cannot be topologically sorted.")
        return order
