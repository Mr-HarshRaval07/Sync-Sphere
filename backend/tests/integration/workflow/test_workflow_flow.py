import pytest
from fastapi.testclient import TestClient
from syncsphere.main import app

client = TestClient(app)

def test_workflow_full_api_lifecycle_flow():
    """Tests the full API workflow designer journey: create, edit, validate, compile, publish, clone, export, import."""
    
    # 1. Login user to get JWT Admin token
    register_payload = {
        "email": "admin4@acme.ai",
        "password": "supersecretpassword123!",
        "first_name": "Dave",
        "last_name": "Adams",
        "org_name": "Acme Corp 4",
        "org_slug": "acme-corp-4"
    }
    client.post("/v1/auth/register", json=register_payload)
    
    resp_login = client.post("/v1/auth/login", json={"email": "admin4@acme.ai", "password": "supersecretpassword123!"})
    access_token = resp_login.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    # 2. Create Workflow config
    create_payload = {
        "name": "Process Escalations",
        "description": "Orchestrates Slack and Jira escalations."
    }
    resp_create = client.post("/v1/workflows", json=create_payload, headers=headers)
    assert resp_create.status_code == 201
    wf_data = resp_create.json()["data"]
    wf_id = wf_data["id"]
    assert wf_data["name"] == "Process Escalations"
    assert wf_data["status"] == "DRAFT"

    # 3. Patch Update graph structure with nodes and edges
    # Build n1 -> n2
    update_payload = {
        "nodes": {
            "n1": {
                "id": "n1",
                "name": "Get Support Ticket",
                "type": "tool_call"
            },
            "n2": {
                "id": "n2",
                "name": "Notify Developer Channel",
                "type": "tool_call",
                "input_bindings": [
                    {
                        "source_node_id": "n1",
                        "source_field": "summary",
                        "target_field": "message"
                    }
                ]
            }
        },
        "edges": [
            {
                "source_node_id": "n1",
                "target_node_id": "n2"
            }
        ]
    }
    resp_patch = client.patch(f"/v1/workflows/{wf_id}", json=update_payload, headers=headers)
    assert resp_patch.status_code == 200
    wf_updated = resp_patch.json()["data"]
    assert len(wf_updated["nodes"]) == 2
    assert len(wf_updated["edges"]) == 1

    # 4. Perform validation checks
    resp_val = client.post(f"/v1/workflows/{wf_id}/validate", headers=headers)
    assert resp_val.status_code == 200
    assert resp_val.json()["data"]["valid"] is True

    # 5. Compile into execution plan
    resp_comp = client.post(f"/v1/workflows/{wf_id}/compile", headers=headers)
    assert resp_comp.status_code == 200
    comp_data = resp_comp.json()["data"]
    assert comp_data["topological_order"] == ["n1", "n2"]
    assert "n2" in comp_data["execution_nodes"]
    assert comp_data["execution_nodes"]["n2"]["dependencies"] == ["n1"]

    # 6. Publish Version
    pub_payload = {"version_description": "Initial Stable Release"}
    resp_pub = client.post(f"/v1/workflows/{wf_id}/publish", json=pub_payload, headers=headers)
    assert resp_pub.status_code == 200
    pub_data = resp_pub.json()["data"]
    assert pub_data["version"] >= 1
    assert pub_data["description"] == "Initial Stable Release"

    # Verify status changed to PUBLISHED
    resp_get = client.get(f"/v1/workflows/{wf_id}", headers=headers)
    assert resp_get.json()["data"]["status"] == "PUBLISHED"
    assert resp_get.json()["data"]["active_version"] == pub_data["version"]

    # 7. Clone Workflow
    clone_payload = {"new_name": "Process Escalations (Copy)"}
    resp_clone = client.post(f"/v1/workflows/{wf_id}/clone", json=clone_payload, headers=headers)
    assert resp_clone.status_code == 201
    cloned_data = resp_clone.json()["data"]
    assert cloned_data["name"] == "Process Escalations (Copy)"
    assert cloned_data["status"] == "DRAFT"

    # 8. Export Configuration
    resp_exp = client.get(f"/v1/workflows/{wf_id}/export", headers=headers)
    assert resp_exp.status_code == 200
    export_schema = resp_exp.json()["data"]
    assert export_schema["name"] == "Process Escalations"
    assert len(export_schema["nodes"]) == 2

    # 9. Import Configuration
    export_schema["name"] = "Imported Process Workflow"
    resp_imp = client.post("/v1/workflows/import", json=export_schema, headers=headers)
    assert resp_imp.status_code == 201
    imp_data = resp_imp.json()["data"]
    assert imp_data["name"] == "Imported Process Workflow"
    assert len(imp_data["nodes"]) == 2

    # 10. Delete Original Workflow
    resp_del = client.delete(f"/v1/workflows/{wf_id}", headers=headers)
    assert resp_del.status_code == 204
