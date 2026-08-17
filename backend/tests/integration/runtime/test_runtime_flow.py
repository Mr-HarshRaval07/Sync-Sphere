import pytest
import time
from fastapi.testclient import TestClient
from syncsphere.main import app

client = TestClient(app)

def test_runtime_api_lifecycle_flow():
    """Integration test verifying full runtime endpoint actions: execute workflow, verify state, check traces and checkpoints."""
    
    # 1. Login user to get JWT Admin token
    register_payload = {
        "email": "runtime_admin@acme.ai",
        "password": "supersecretpassword123!",
        "first_name": "Execution",
        "last_name": "Tester",
        "org_name": "Acme Runtime",
        "org_slug": "acme-runtime"
    }
    client.post("/v1/auth/register", json=register_payload)
    
    resp_login = client.post("/v1/auth/login", json={"email": "runtime_admin@acme.ai", "password": "supersecretpassword123!"})
    access_token = resp_login.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    # 2. Create Workflow
    create_payload = {
        "name": "Integration Runtime Flow",
        "description": "Orchestrates API execution flow tests."
    }
    resp_create = client.post("/v1/workflows", json=create_payload, headers=headers)
    assert resp_create.status_code == 201
    wf_id = resp_create.json()["data"]["id"]

    # 3. Patch Update graph structure with nodes
    update_payload = {
        "nodes": {
            "step_1": {
                "id": "step_1",
                "name": "First Action",
                "type": "tool_call"
            },
            "step_2": {
                "id": "step_2",
                "name": "Second Action",
                "type": "tool_call",
                "input_bindings": [
                    {
                        "source_node_id": "step_1",
                        "source_field": "result",
                        "target_field": "val"
                    }
                ]
            }
        },
        "edges": [
            {
                "source_node_id": "step_1",
                "target_node_id": "step_2"
            }
        ]
    }
    resp_patch = client.patch(f"/v1/workflows/{wf_id}", json=update_payload, headers=headers)
    assert resp_patch.status_code == 200

    # 4. Publish version
    pub_payload = {"version_description": "Runtime V1"}
    resp_pub = client.post(f"/v1/workflows/{wf_id}/publish", json=pub_payload, headers=headers)
    assert resp_pub.status_code == 200

    # 5. Launch execution session
    exec_payload = {
        "workflow_id": wf_id,
        "inputs": {"initial_key": "initial_value"},
        "policy": "BalancedExecution"
    }
    resp_exec = client.post("/v1/runtime/start", json=exec_payload, headers=headers)
    assert resp_exec.status_code == 201
    exec_data = resp_exec.json()["data"]
    session_id = exec_data["session_id"]
    assert exec_data["workflow_id"] == wf_id
    assert exec_data["status"] in ("CREATED", "QUEUED", "RUNNING", "COMPLETED")

    # Give it a tiny sleep to execute in background
    time.sleep(0.1)

    # 6. Retrieve execution session details
    resp_get_session = client.get(f"/v1/runtime/status/{session_id}", headers=headers)
    assert resp_get_session.status_code == 200
    session_details = resp_get_session.json()["data"]
    assert session_details["session_id"] == session_id
    assert session_details["variables"]["initial_key"] == "initial_value"

    # 7. Retrieve execution trace/history details
    resp_get_trace = client.get(f"/v1/runtime/history/{session_id}", headers=headers)
    assert resp_get_trace.status_code == 200
    trace_details = resp_get_trace.json()["data"]
    assert trace_details["session_id"] == session_id
    assert isinstance(trace_details["events"], list)

    # 8. Retrieve logs
    resp_get_logs = client.get(f"/v1/runtime/logs/{session_id}", headers=headers)
    assert resp_get_logs.status_code == 200
    logs_list = resp_get_logs.json()["data"]
    assert isinstance(logs_list, list)
