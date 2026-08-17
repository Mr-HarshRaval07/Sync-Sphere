import logging
import uuid
from typing import List, Dict, Any, Optional
from syncsphere.planner.domain.value_objects import PlanAST, ASTNode
from syncsphere.workflow.domain.entities.workflow import Workflow
from syncsphere.workflow.domain.entities.workflow_version import WorkflowVersion
from syncsphere.workflow.domain.value_objects import (
    WorkflowGraph,
    WorkflowNode,
    WorkflowEdge,
    WorkflowStepType,
    Variable,
    VariableType,
    ConnectorBinding,
    ToolInvocation,
    ApprovalGate,
    RetryPolicy,
    TimeoutPolicy,
    InputBinding,
    OutputBinding,
    ExecutionPlan
)
from syncsphere.workflow.infrastructure.dag.compiler import WorkflowCompiler as SharedCompiler

logger = logging.getLogger("syncsphere.planner.domain.services.compiler")

class ApprovalGateInserter:
    """Injects human-in-the-loop ApprovalGate steps before high-risk destructive operations."""
    @staticmethod
    def inject_approval(graph: WorkflowGraph, risk_level: str) -> None:
        target_node_ids = []
        risky_terms = ["delete", "remove", "destroy", "prune", "send", "create", "post", "append", "pay", "charge"]
        
        for nid, node in list(graph.nodes.items()):
            if node.type == WorkflowStepType.TOOL_CALL and node.tool_invocation:
                tool_name = node.tool_invocation.tool_name.lower()
                if risk_level == "high" or any(term in tool_name for term in risky_terms):
                    target_node_ids.append(nid)
                    
        for target_id in target_node_ids:
            app_node_id = f"approve_{target_id}"
            target_node = graph.nodes[target_id]
            
            # Create Approval Node
            app_node = WorkflowNode(
                id=app_node_id,
                name=f"Approve {target_node.name}",
                type=WorkflowStepType.APPROVAL,
                approval_gate=ApprovalGate(
                    title=f"Review Action: {target_node.name}",
                    description=f"Auto-inserted Human Approval gate for risky action: {target_node.name} (Risk matches policy).",
                    instructions="Please review carefully before proceeding.",
                    approvers=["admin@acme.ai"]
                )
            )
            graph.nodes[app_node_id] = app_node
            
            # Redirect edges: any edge going into target_id now goes into app_node_id.
            redirected_source_ids = []
            new_edges = []
            for edge in graph.edges:
                if edge.target_node_id == target_id:
                    edge.target_node_id = app_node_id
                    redirected_source_ids.append(edge.source_node_id)
                new_edges.append(edge)
                
            # Connect app_node to target_id
            new_edges.append(WorkflowEdge(
                source_node_id=app_node_id,
                target_node_id=target_id
            ))
            graph.edges = new_edges


class GraphBuilder:
    """Compiles PlanAST structures into pure WorkflowGraph structures."""
    @staticmethod
    def build_graph(ast: PlanAST) -> WorkflowGraph:
        nodes = {}
        edges = []
        
        for ast_node in ast.nodes:
            # Map Step Type
            step_type = WorkflowStepType.TOOL_CALL
            if ast_node.type == "condition":
                step_type = WorkflowStepType.CONDITION
            elif ast_node.type == "approval":
                step_type = WorkflowStepType.APPROVAL
            elif ast_node.type == "delay":
                step_type = WorkflowStepType.DELAY
            elif ast_node.type == "transform":
                step_type = WorkflowStepType.TRANSFORM
                
            tool_invocation = None
            if ast_node.connector_id and ast_node.tool_name:
                tool_invocation = ToolInvocation(
                    connector_binding=ConnectorBinding(connector_id=ast_node.connector_id),
                    tool_name=ast_node.tool_name,
                    arguments_map=ast_node.arguments
                )
                
            # Build input bindings
            input_bindings = []
            for input_var in ast_node.inputs:
                if input_var.binding_expression:
                    # e.g. "step_id.output_field"
                    parts = input_var.binding_expression.split(".")
                    if len(parts) >= 2:
                        input_bindings.append(InputBinding(
                            source_node_id=parts[0],
                            source_field=parts[1],
                            target_field=input_var.name
                        ))
                        
            node = WorkflowNode(
                id=ast_node.node_id,
                name=ast_node.name,
                type=step_type,
                tool_invocation=tool_invocation,
                input_bindings=input_bindings,
                retry_policy=RetryPolicy(max_attempts=3, backoff_factor=2.0, initial_interval_seconds=2),
                timeout_policy=TimeoutPolicy(timeout_seconds=300)
            )
            nodes[ast_node.node_id] = node
            
            # Map edges
            for dep in ast_node.depends_on:
                edges.append(WorkflowEdge(
                    source_node_id=dep,
                    target_node_id=ast_node.node_id
                ))
                
        return WorkflowGraph(nodes=nodes, edges=edges)


class VariableBinder:
    """Maps dynamic variables and parameters in the compiled workflow."""
    @staticmethod
    def bind_variables(ast: PlanAST) -> List[Variable]:
        variables = []
        for var in ast.variables:
            var_type = VariableType.STRING
            if var.type == "number":
                var_type = VariableType.NUMBER
            elif var.type == "boolean":
                var_type = VariableType.BOOLEAN
            elif var.type == "object":
                var_type = VariableType.OBJECT
            elif var.type == "array":
                var_type = VariableType.ARRAY
                
            variables.append(Variable(
                name=var.name,
                type=var_type,
                default_val=var.value
            ))
        return variables


class WorkflowCompiler:
    """Translates PlanAST to Workflow aggregates and schedules ExecutionPlans."""
    @staticmethod
    def compile_workflow(
        org_id: str,
        name: str,
        description: str,
        ast: PlanAST,
        risk_level: str = "low"
    ) -> tuple:
        # 1. Build Graph
        graph = GraphBuilder.build_graph(ast)
        
        # 2. Inject Approval Gates if high risk
        ApprovalGateInserter.inject_approval(graph, risk_level)
        
        # 3. Bind variables
        variables = VariableBinder.bind_variables(ast)
        
        # 4. Synthesize Workflow Aggregate
        workflow = Workflow(
            org_id=org_id,
            name=name,
            description=description,
            graph=graph,
            variables=variables
        )
        # Assign generated ID to enable version mappings
        workflow.id = str(uuid.uuid4())
        
        # 5. Compile Version
        version = workflow.publish("Initial auto-generated blueprint version")
        version.id = str(uuid.uuid4())
        
        # 6. Build execution plan using SharedCompiler
        execution_plan = SharedCompiler.compile(workflow)
        
        return workflow, version, execution_plan
