import logging
from typing import List, Dict, Any
from syncsphere.runtime.domain.value_objects import (
    ExecutionAST,
    ASTNode,
    ExecutionPolicy,
    ExecutionState,
    ExecutionStep
)
from syncsphere.runtime.domain.entities.session import ExecutionSession
from syncsphere.workflow.domain.value_objects import ExecutionPlan

logger = logging.getLogger("syncsphere.runtime.application.services.scheduler")

class DependencyResolver:
    """Evaluates DAG node dependencies to determine which steps are ready for invocation."""
    
    @staticmethod
    def resolve_ready_nodes(session: ExecutionSession, ast: ExecutionAST) -> List[str]:
        """Returns list of node IDs that are ready (all direct dependencies are COMPLETED)."""
        ready = []
        for node_id, node in ast.nodes.items():
            # If the node is already queued, running, completed, or failed, skip it
            step = session.steps.get(node_id)
            if step and step.status in (
                ExecutionState.QUEUED,
                ExecutionState.RUNNING,
                ExecutionState.COMPLETED,
                ExecutionState.FAILED,
                ExecutionState.AWAITING_APPROVAL,
                ExecutionState.RETRYING
            ):
                continue
                
            # Check if all dependency steps are COMPLETED
            deps_met = True
            for dep_id in node.dependencies:
                dep_step = session.steps.get(dep_id)
                if not dep_step or dep_step.status != ExecutionState.COMPLETED:
                    deps_met = False
                    break
                    
            if deps_met:
                ready.append(node_id)
                
        return ready

class ExecutionScheduler:
    """Compiles the initial ExecutionAST and manages task schedules according to execution policy."""
    
    @staticmethod
    def build_ast(plan: ExecutionPlan) -> ExecutionAST:
        """Derives a mutable runtime ExecutionAST from an immutable compilation ExecutionPlan."""
        nodes = {}
        for node_id, plan_node in plan.execution_nodes.items():
            nodes[node_id] = ASTNode(
                node_id=node_id,
                name=plan_node.name,
                type=plan_node.type.value,
                dependencies=plan_node.dependencies
            )
            
        return ExecutionAST(
            workflow_id=plan.workflow_id,
            version=plan.version,
            nodes=nodes,
            topological_order=plan.topological_order
        )

    @staticmethod
    def filter_by_policy(ready_nodes: List[str], policy: ExecutionPolicy) -> List[str]:
        """Filters ready nodes based on ExecutionPolicy resource restrictions."""
        if not ready_nodes:
            return []
            
        if policy == ExecutionPolicy.LOW_MEMORY or policy == ExecutionPolicy.SAFE:
            # Execute only one node at a time (sequential execution)
            return [ready_nodes[0]]
            
        # Balanced or Aggressive Parallel allows multi-node concurrently
        return ready_nodes
