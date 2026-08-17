import logging
from typing import Dict, Any, List
from syncsphere.workflow.domain.entities.workflow import Workflow
from syncsphere.workflow.domain.value_objects import ExecutionPlan, ExecutionNode, WorkflowGraph
from syncsphere.workflow.infrastructure.dag.validator import DAGValidator

logger = logging.getLogger("syncsphere.workflow.infrastructure.dag.compiler")

class WorkflowCompiler:
    """Compiles a Workflow domain model into a structured, runnable ExecutionPlan."""

    @staticmethod
    def compile(workflow: Workflow) -> ExecutionPlan:
        """
        Validates DAG constraints and compiles the workflow draft
        into a static topological ExecutionPlan.
        """
        logger.info("Compiling workflow '%s' (ID: %s)", workflow.name, workflow.id)
        
        # 1. Structural graph validation
        DAGValidator.validate(workflow.graph, workflow.variables)

        # 2. Get Topological Sort Order
        topo_order = DAGValidator.topological_sort(workflow.graph)

        # 3. Build Node dependencies mapping
        # Maps target_node_id to list of source_node_ids
        dependencies: Dict[str, List[str]] = {nid: [] for nid in workflow.graph.nodes}
        for edge in workflow.graph.edges:
            if edge.target_node_id in dependencies:
                dependencies[edge.target_node_id].append(edge.source_node_id)

        # 4. Map WorkflowNodes to ExecutionNodes
        execution_nodes = {}
        for nid, node in workflow.graph.nodes.items():
            execution_nodes[nid] = ExecutionNode(
                node_id=node.id,
                name=node.name,
                type=node.type,
                dependencies=dependencies[node.id]
            )

        # Compile version to snapshot (if draft, version is 0)
        version_num = workflow.active_version or 0

        return ExecutionPlan(
            workflow_id=workflow.id,
            version=version_num,
            topological_order=topo_order,
            execution_nodes=execution_nodes
        )
