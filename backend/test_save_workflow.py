import asyncio
import uuid
import datetime
from syncsphere.workflow.presentation.schemas import UpdateWorkflowRequest, WorkflowNode, WorkflowEdge
from syncsphere.workflow.domain.value_objects import ToolInvocation, ConnectorBinding
from pydantic import ValidationError

def test_validation():
    try:
        nodes = {
            "start_1": {
                "id": "start_1",
                "type": "start",
                "position": {"x": 100, "y": 100},
                "data": {"config": {}}
            },
            "ai_planner_1": {
                "id": "ai_planner_1",
                "type": "planner",
                "position": {"x": 100, "y": 100},
                "data": {"config": {}}
            }
        }
        edges = [
            {
                "id": "e1",
                "source_node_id": "start_1",
                "target_node_id": "ai_planner_1",
                "type": "smoothstep"
            }
        ]
        
        req = UpdateWorkflowRequest(nodes=nodes, edges=edges)
        print("Success! Request parsed correctly.")
    except ValidationError as e:
        print("ValidationError:", e)

if __name__ == "__main__":
    test_validation()
