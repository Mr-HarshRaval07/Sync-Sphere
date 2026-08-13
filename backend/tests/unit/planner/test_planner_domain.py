import pytest
from typing import Dict, List, Any
from syncsphere.planner.domain.value_objects import (
    PlanningStep,
    PlanAST,
    ASTNode,
    ASTVariable,
    ConfidenceScore,
    RiskAssessment,
    PlanningContext
)
from syncsphere.planner.domain.entities import PlanningSession, PlannerTrace
from syncsphere.planner.domain.services.reasoning import (
    DependencyResolver,
    ParallelismAnalyzer,
    WorkflowSynthesizer,
    PlannerReflectionEngine,
    ReasoningEngine
)
from syncsphere.planner.domain.services.connector_intel import (
    CapabilityMatcher,
    CompatibilityValidator,
    ToolCandidate
)
from syncsphere.connectors.domain.value_objects import ToolDefinition
from syncsphere.planner.domain.services.compiler import WorkflowCompiler
from syncsphere.planner.domain.services.optimizer import GraphOptimizer
from syncsphere.planner.domain.services.validator import WorkflowValidator
from syncsphere.shared_kernel.domain.domain_exception import ValidationException
from syncsphere.workflow.domain.value_objects import WorkflowStepType


def test_dependency_resolver_and_cycle_detection():
    # Linear steps
    steps = [
        PlanningStep(step_id="step_a", name="A", description="A desc", capability_required="cap_a"),
        PlanningStep(step_id="step_b", name="B", description="B desc", capability_required="cap_b", depends_on_steps=["step_a"]),
    ]
    resolved = DependencyResolver.resolve_dependencies(steps)
    assert len(resolved) == 2
    
    # Cyclic steps
    cyclic_steps = [
        PlanningStep(step_id="step_a", name="A", description="A desc", capability_required="cap_a", depends_on_steps=["step_b"]),
        PlanningStep(step_id="step_b", name="B", description="B desc", capability_required="cap_b", depends_on_steps=["step_a"]),
    ]
    with pytest.raises(ValueError, match="Cyclic dependency detected"):
        DependencyResolver.resolve_dependencies(cyclic_steps)


def test_parallelism_analyzer():
    steps = [
        PlanningStep(step_id="step_a", name="A", description="A desc", capability_required="cap_a"),
        PlanningStep(step_id="step_b", name="B", description="B desc", capability_required="cap_b"),
        PlanningStep(step_id="step_c", name="C", description="C desc", capability_required="cap_c", depends_on_steps=["step_a", "step_b"]),
        PlanningStep(step_id="step_d", name="D", description="D desc", capability_required="cap_d", depends_on_steps=["step_c"]),
    ]
    tiers = ParallelismAnalyzer.analyze_parallelism(steps)
    assert len(tiers) == 3
    assert set(tiers[0]) == {"step_a", "step_b"}
    assert tiers[1] == ["step_c"]
    assert tiers[2] == ["step_d"]


def test_capability_matcher():
    tools = [
        ToolDefinition(name="post_message", description="Sends slack message to channel", input_schema={}),
        ToolDefinition(name="delete_database", description="Dangerously deletes a database", input_schema={}),
    ]
    
    candidates = CapabilityMatcher.calculate_match("step1", "post_message", tools, "conn_1")
    assert len(candidates) > 0
    assert candidates[0].tool_name == "post_message"
    assert candidates[0].score == 1.0
    
    # Check approximate description match
    desc_candidates = CapabilityMatcher.calculate_match("step1", "slack message", tools, "conn_1")
    assert len(desc_candidates) > 0
    assert desc_candidates[0].tool_name == "post_message"
    assert desc_candidates[0].score > 0.0


def test_graph_optimization():
    # Test redundancy removal and dead-node elimination
    # Set up nodes: node2 is a duplicate of node1
    ast = PlanAST(
        variables=[],
        nodes=[
            ASTNode(node_id="node1", name="N1", connector_id="conn1", tool_name="tool_a", arguments={"msg": "hello"}),
            ASTNode(node_id="node2", name="N2", connector_id="conn1", tool_name="tool_a", arguments={"msg": "hello"}),
            ASTNode(node_id="node3", name="N3", connector_id="conn2", tool_name="tool_b", depends_on=["node2"]),
        ]
    )
    ast.flows.entry_nodes = ["node1", "node2"]
    
    optimized_nodes, cost, latency = GraphOptimizer.optimize_graph(ast)
    assert "node2" in optimized_nodes
    assert len(ast.nodes) == 2
    # node3 should now depend on node1 because node2 was pruned and dependencies redirected
    surviving_nodes = {n.node_id: n for n in ast.nodes}
    assert "node1" in surviving_nodes
    assert "node3" in surviving_nodes
    assert "node1" in surviving_nodes["node3"].depends_on


def test_approval_gate_injection_and_workflow_compilation():
    ast = PlanAST(
        variables=[
            ASTVariable(name="project_key", type="string", value="PROJ")
        ],
        nodes=[
            ASTNode(node_id="delete_step", name="Prune DB", connector_id="conn_1", tool_name="delete_data", arguments={}),
        ]
    )
    
    # High risk triggering approval gate injection
    wf, version, plan = WorkflowCompiler.compile_workflow(
        org_id="org_1",
        name="Destructive workflow",
        description="Auto-generated high risk",
        ast=ast,
        risk_level="high"
    )
    
    # The approval gate should have been injected
    assert len(wf.graph.nodes) == 2
    assert "approve_delete_step" in wf.graph.nodes
    app_node = wf.graph.nodes["approve_delete_step"]
    assert app_node.type == WorkflowStepType.APPROVAL
    
    # Edges should point from approval node to the destructive node
    assert len(wf.graph.edges) == 1
    assert wf.graph.edges[0].source_node_id == "approve_delete_step"
    assert wf.graph.edges[0].target_node_id == "delete_step"


def test_validator():
    # Valid workflow check
    # Let's import the default validator and verify checking constraints
    from syncsphere.workflow.domain.entities.workflow import Workflow
    from syncsphere.workflow.domain.value_objects import WorkflowNode, WorkflowStepType
    wf = Workflow(org_id="org_1", name="Valid Workflow")
    wf.add_node(WorkflowNode(id="node_1", name="Action", type=WorkflowStepType.TOOL_CALL))
    
    confidence = ConfidenceScore(
        intent_confidence=0.8,
        connector_confidence=0.9,
        tool_confidence=0.85,
        step_confidence=0.85,
        overall_confidence=0.85
    )
    
    risk = RiskAssessment(
        safety_score=1.0,
        risk_level="low"
    )
    
    # Low confidence raises error
    low_confidence = ConfidenceScore(
        intent_confidence=0.3,
        connector_confidence=0.3,
        tool_confidence=0.3,
        step_confidence=0.3,
        overall_confidence=0.3
    )
    with pytest.raises(ValidationException, match="Overall planner confidence"):
        WorkflowValidator.validate_workflow(wf, low_confidence, risk, 0.05)
        
    # High risk raises error
    high_risk = RiskAssessment(
        safety_score=0.2,
        risk_level="high",
        identified_risks=["Critical deletion risk without safety checks"]
    )
    with pytest.raises(ValidationException, match="Plan safety score too low"):
        WorkflowValidator.validate_workflow(wf, confidence, high_risk, 0.05)

    # Cost limit exceeded raises error
    with pytest.raises(ValidationException, match="Estimated planning execution cost"):
        WorkflowValidator.validate_workflow(wf, confidence, risk, 25.0)
