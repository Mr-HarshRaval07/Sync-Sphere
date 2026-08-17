import logging
from typing import List, Dict, Any
from syncsphere.planner.domain.value_objects import PlanAST, ASTNode, ASTFlow

logger = logging.getLogger("syncsphere.planner.domain.services.optimizer")

class ParallelizationOptimizer:
    """Groups independent execution nodes into concurrent stages."""
    @staticmethod
    def optimize(ast: PlanAST) -> None:
        # Re-order and verify that parallel paths are grouped by in-degrees
        # (This is implicitly resolved by compile phase, but can optimize flow representation)
        pass


class RedundancyRemover:
    """Identifies and eliminates identical tool calls, merging their outputs."""
    @staticmethod
    def optimize(ast: PlanAST) -> List[str]:
        removed_node_ids = []
        unique_calls = {}  # key -> node_id (key: (connector_id, tool_name, str(sorted_args)))
        
        surviving_nodes = []
        # Maps duplicate node_id to surviving node_id
        redirect_map = {}
        
        for node in ast.nodes:
            if node.connector_id and node.tool_name:
                arg_key = str(sorted(node.arguments.items()))
                key = (node.connector_id, node.tool_name, arg_key)
                
                if key in unique_calls:
                    # Redundant node found!
                    surviving_id = unique_calls[key]
                    redirect_map[node.node_id] = surviving_id
                    removed_node_ids.append(node.node_id)
                else:
                    unique_calls[key] = node.node_id
                    surviving_nodes.append(node)
            else:
                surviving_nodes.append(node)
                
        # Redirect dependencies in surviving nodes
        for node in surviving_nodes:
            new_deps = []
            for dep in node.depends_on:
                if dep in redirect_map:
                    # Redirect dependency to the survivor
                    new_deps.append(redirect_map[dep])
                else:
                    new_deps.append(dep)
            node.depends_on = list(set(new_deps))
            
        ast.nodes = surviving_nodes
        return removed_node_ids


class DeadNodeEliminator:
    """Removes orphaned steps that do not connect to the execution pathways."""
    @staticmethod
    def optimize(ast: PlanAST) -> List[str]:
        # Simple dead node elimination: if a node is not an entry node, and has no incoming edges,
        # or if it is not reachable from the entry nodes, we can prune it.
        # Find all reachable nodes from entry nodes using BFS
        entry_nodes = ast.flows.entry_nodes
        if not entry_nodes:
            return []
            
        reachable = set(entry_nodes)
        queue = list(entry_nodes)
        
        # Build adjacency mapping (source -> list of targets)
        adj = {node.node_id: [] for node in ast.nodes}
        for node in ast.nodes:
            for dep in node.depends_on:
                if dep in adj:
                    adj[dep].append(node.node_id)
                    
        while queue:
            curr = queue.pop(0)
            for neighbor in adj.get(curr, []):
                if neighbor not in reachable:
                    reachable.add(neighbor)
                    queue.append(neighbor)
                    
        pruned_ids = []
        surviving = []
        for node in ast.nodes:
            if node.node_id in reachable:
                surviving.append(node)
            else:
                pruned_ids.append(node.node_id)
                
        ast.nodes = surviving
        return pruned_ids


class GraphOptimizer:
    """Coordinates parallel execution, redundant prunes, and dead-node elimination runs."""
    @staticmethod
    def optimize_graph(ast: PlanAST) -> tuple:
        removed_redundant = RedundancyRemover.optimize(ast)
        removed_dead = DeadNodeEliminator.optimize(ast)
        ParallelizationOptimizer.optimize(ast)
        
        # Calculate cost saving (e.g. mock $0.05 saved per redundant tool removed)
        cost_saving = (len(removed_redundant) + len(removed_dead)) * 0.05
        latency_saving = (len(removed_redundant) + len(removed_dead)) * 250.0
        
        return removed_redundant + removed_dead, cost_saving, latency_saving
