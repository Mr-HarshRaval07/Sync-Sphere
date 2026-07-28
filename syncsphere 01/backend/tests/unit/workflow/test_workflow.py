import pytest
from syncsphere.workflow.domain.entities.workflow import Workflow
from syncsphere.workflow.domain.value_objects import (
    WorkflowStatus,
    WorkflowNode,
    WorkflowStepType,
    WorkflowEdge
)

def test_workflow_creation():
    """Tests that a Workflow starts with correct defaults."""
    wf = Workflow(org_id="org_123", name="Alert Router")
    assert wf.org_id == "org_123"
    assert wf.name == "Alert Router"
    assert wf.status == WorkflowStatus.DRAFT
    assert wf.active_version is None
    assert wf.latest_version == 0
    assert len(wf.graph.nodes) == 0

def test_workflow_graph_manipulations():
    """Tests adding nodes and edges to the draft graph."""
    wf = Workflow(org_id="org_123", name="Alert Router")
    node1 = WorkflowNode(id="node_1", name="Jira Step", type=WorkflowStepType.TOOL_CALL)
    node2 = WorkflowNode(id="node_2", name="Slack Step", type=WorkflowStepType.TOOL_CALL)
    
    wf.add_node(node1)
    wf.add_node(node2)
    assert len(wf.graph.nodes) == 2
    assert "node_1" in wf.graph.nodes

    # Add edge
    edge = WorkflowEdge(source_node_id="node_1", target_node_id="node_2")
    wf.add_edge(edge)
    assert len(wf.graph.edges) == 1
    
    # Remove node cleans up dangling edge references
    wf.remove_node("node_1")
    assert len(wf.graph.nodes) == 1
    assert len(wf.graph.edges) == 0

def test_workflow_publish_and_clone():
    """Tests creating version snapshots and cloning operations."""
    wf = Workflow(org_id="org_123", name="Alert Router")
    node = WorkflowNode(id="node_1", name="Jira Step", type=WorkflowStepType.TOOL_CALL)
    wf.add_node(node)
    
    # Publish version 1
    snap = wf.publish("Initial release")
    assert wf.status == WorkflowStatus.PUBLISHED
    assert wf.active_version == 1
    assert wf.latest_version == 1
    assert snap.version == 1
    assert "node_1" in snap.graph.nodes
    
    # Clone workflow
    cloned = wf.clone("Alert Router v2")
    assert cloned.name == "Alert Router v2"
    assert cloned.status == WorkflowStatus.DRAFT
    assert cloned.active_version is None
    assert "node_1" in cloned.graph.nodes
