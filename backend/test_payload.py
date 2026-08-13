import asyncio
from syncsphere.workflow.presentation.schemas import UpdateWorkflowRequest

payload = {
    "name": "Copy of test",
    "description": "test",
    "nodes": {
        "start_1": {
            "id": "start_1",
            "name": "On Task Activity",
            "type": "transform",
            "retry_policy": {"max_attempts": 3, "backoff_factor": 2.0, "initial_interval_seconds": 2},
            "timeout_policy": {"timeout_seconds": 300},
            "compensation_policy": {"compensation_node_id": None, "parameters_mapping": {}},
            "input_bindings": [],
            "output_bindings": []
        },
        "ai_planner_1": {
            "id": "ai_planner_1",
            "name": "AI Project Manager",
            "type": "tool_call",
            "tool_invocation": {
                "connector_binding": {
                    "connector_id": "unknown",
                    "scopes_override": []
                },
                "tool_name": "planner",
                "arguments_map": {}
            },
            "retry_policy": {"max_attempts": 3, "backoff_factor": 2.0, "initial_interval_seconds": 2},
            "timeout_policy": {"timeout_seconds": 300},
            "compensation_policy": {"compensation_node_id": None, "parameters_mapping": {}},
            "input_bindings": [],
            "output_bindings": []
        },
        "cond_final": {
            "id": "cond_final",
            "name": "Check Status",
            "type": "condition",
            "condition": {
                "left_operand": "",
                "operator": "EQUAL",
                "right_operand": ""
            },
            "retry_policy": {"max_attempts": 3, "backoff_factor": 2.0, "initial_interval_seconds": 2},
            "timeout_policy": {"timeout_seconds": 300},
            "compensation_policy": {"compensation_node_id": None, "parameters_mapping": {}},
            "input_bindings": [],
            "output_bindings": []
        }
    },
    "edges": [
        {
            "source_node_id": "start_1",
            "target_node_id": "ai_planner_1",
            "condition_expression": None
        }
    ],
    "variables": []
}

try:
    req = UpdateWorkflowRequest(**payload)
    print("SUCCESS")
except Exception as e:
    print("FAILED:", e)
