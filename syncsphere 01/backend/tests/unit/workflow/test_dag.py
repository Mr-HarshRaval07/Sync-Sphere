import pytest
from syncsphere.workflow.domain.value_objects import WorkflowGraph, WorkflowNode, WorkflowStepType, WorkflowEdge
from syncsphere.workflow.infrastructure.dag.validator import CycleDetector, DAGValidator
from syncsphere.workflow.domain.exceptions import InvalidWorkflowGraphException

def test_dag_cycle_detection_and_validation():
    """Tests cycle detector blocks cyclic configurations, and parses correct sorted order."""
    graph = WorkflowGraph()
    n1 = WorkflowNode(id="n1", name="Step 1", type=WorkflowStepType.TOOL_CALL)
    n2 = WorkflowNode(id="n2", name="Step 2", type=WorkflowStepType.TOOL_CALL)
    n3 = WorkflowNode(id="n3", name="Step 3", type=WorkflowStepType.TOOL_CALL)
    
    graph.nodes = {"n1": n1, "n2": n2, "n3": n3}
    
    # 1. Connected Graph n1 -> n2 -> n3 (No cycle)
    graph.edges = [
        WorkflowEdge(source_node_id="n1", target_node_id="n2"),
        WorkflowEdge(source_node_id="n2", target_node_id="n3")
    ]
    assert CycleDetector.has_cycle(graph) is False
    
    topo_order = DAGValidator.topological_sort(graph)
    assert topo_order == ["n1", "n2", "n3"]
    
    DAGValidator.validate(graph) # Should pass

    # 2. Add cyclic edge n3 -> n1
    graph.edges.append(WorkflowEdge(source_node_id="n3", target_node_id="n1"))
    assert CycleDetector.has_cycle(graph) is True
    
    with pytest.raises(InvalidWorkflowGraphException) as exc:
        DAGValidator.validate(graph)
    assert "Cycle detected" in str(exc.value)

def test_dag_binding_causality_checks():
    """Tests validator rejects input mapping references from downstream nodes."""
    graph = WorkflowGraph()
    n1 = WorkflowNode(id="n1", name="Step 1", type=WorkflowStepType.TOOL_CALL)
    n2 = WorkflowNode(id="n2", name="Step 2", type=WorkflowStepType.TOOL_CALL)
    
    # Add input binding mapping inputs from n2 back into n1 (impossible, since n1 executes first)
    from syncsphere.workflow.domain.value_objects import InputBinding
    invalid_binding = InputBinding(source_node_id="n2", source_field="output_data", target_field="input_data")
    n1.input_bindings = [invalid_binding]
    
    graph.nodes = {"n1": n1, "n2": n2}
    graph.edges = [WorkflowEdge(source_node_id="n1", target_node_id="n2")]
    
    # Validation should reject due to downstream reference (n2 executes after n1)
    with pytest.raises(InvalidWorkflowGraphException) as exc:
        DAGValidator.validate(graph)
    assert "references downstream" in str(exc.value)
