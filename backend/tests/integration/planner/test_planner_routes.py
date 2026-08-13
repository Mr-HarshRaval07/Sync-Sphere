import pytest
from fastapi.testclient import TestClient
from syncsphere.main import app
from syncsphere.core.dependency_injection.container import container
from syncsphere.ai.domain.value_objects import StructuredOutputResult
from syncsphere.connectors.domain.entities.connector import Connector
from syncsphere.connectors.domain.value_objects import ToolDefinition

client = TestClient(app)

def test_planner_endpoints_integration_flow():
    # 1. Register and Login to get auth token
    register_payload = {
        "email": "planner_admin@acme.ai",
        "password": "supersecretpassword123!",
        "first_name": "Alice",
        "last_name": "Planner",
        "org_name": "Acme Planner Corp",
        "org_slug": "acme-planner-corp"
    }
    client.post("/v1/auth/register", json=register_payload)
    
    resp_login = client.post("/v1/auth/login", json={"email": "planner_admin@acme.ai", "password": "supersecretpassword123!"})
    access_token = resp_login.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}
    
    resp_me = client.get("/v1/users/me", headers=headers)
    org_id = resp_me.json()["data"]["org_id"]
    
    # 2. Add an active tool connector to the stub repo
    mock_connector = Connector(
        org_id=org_id,
        name="Jira Connector",
        transport_type="stdio",
        connection_config={}
    )
    mock_connector.tools = [
        ToolDefinition(name="create_issue", description="Creates new Jira issue", input_schema={})
    ]
    # Synchronously saving using the asyncio event loop under anyio/asyncio:
    # Since we are in a synchronous test function but container repositories are async,
    # and conftest clean_repositories setup event loops, we can mock/run:
    import asyncio
    asyncio.run(container.connector_repo.save(mock_connector))
    
    # 3. Mock AI Gateway structured output
    async def mock_structured_output(org_id, messages, schema, policy, settings=None, correlation_id=None):
        name = schema.schema_name
        if name == "IntentClassification":
            return StructuredOutputResult(
                success=True,
                parsed_object={
                    "category": "workflow_generation",
                    "confidence_score": 0.9,
                    "reasoning": "Intent to generate workflow",
                    "primary_goal": "Create Jira issue"
                }
            )
        elif name == "EntityExtraction":
            return StructuredOutputResult(
                success=True,
                parsed_object={"entities": []}
            )
        elif name == "GoalExtraction":
            return StructuredOutputResult(
                success=True,
                parsed_object={
                    "goals": [
                        {"goal_id": "jira_step", "description": "Create ticket", "priority": 1, "dependencies": []}
                    ]
                }
            )
        elif name == "ConstraintExtraction":
            return StructuredOutputResult(
                success=True,
                parsed_object={"constraints": []}
            )
        elif name == "TaskDecomposition":
            return StructuredOutputResult(
                success=True,
                parsed_object={
                    "steps": [
                        {
                            "step_id": "jira_step",
                            "name": "Jira Step",
                            "description": "Create issue in project",
                            "capability_required": "create_issue",
                            "depends_on_steps": [],
                            "arguments": {"project_key": "PROJ"}
                        }
                    ]
                }
            )
        return StructuredOutputResult(success=False, error_message="Unknown schema")
        
    container.ai_gateway.structured_output = mock_structured_output
    
    # 4. Hit POST /v1/planner/validate
    resp_val = client.post(
        "/v1/planner/validate",
        json={"prompt": "Generate a Jira issue template"},
        headers=headers
    )
    assert resp_val.status_code == 200
    val_data = resp_val.json()["data"]
    assert val_data["category"] == "workflow_generation"
    assert val_data["is_valid"] is True

    # 5. Hit POST /v1/planner/generate
    resp_gen = client.post(
        "/v1/planner/generate",
        json={"prompt": "Generate a Jira issue template", "strategy": "simple"},
        headers=headers
    )
    assert resp_gen.status_code == 201
    gen_data = resp_gen.json()["data"]
    wf_id = gen_data["workflow_id"]
    assert gen_data["name"] == "Create Jira issue"
    assert gen_data["nodes_count"] >= 1
    
    # Since session_id is a UUID, we retrieve it from the saved store
    session_id = list(container.planner_session_repo.store.keys())[0]
    
    # 6. Hit GET /v1/planner/preview
    resp_prev = client.get(
        f"/v1/planner/preview?session_id={session_id}",
        headers=headers
    )
    assert resp_prev.status_code == 200
    prev_data = resp_prev.json()["data"]
    assert len(prev_data["nodes"]) == 1
    assert prev_data["nodes"][0]["node_id"] == "jira_step"
    
    # 7. Hit POST /v1/planner/estimate
    resp_est = client.post(
        "/v1/planner/estimate",
        json={"session_id": session_id},
        headers=headers
    )
    assert resp_est.status_code == 200
    est_data = resp_est.json()["data"]
    assert est_data["estimated_cost"] > 0.0
    assert est_data["estimated_time_ms"] > 0.0
    
    # 8. Hit POST /v1/planner/explain
    resp_exp = client.post(
        "/v1/planner/explain",
        json={"session_id": session_id},
        headers=headers
    )
    assert resp_exp.status_code == 200
    exp_data = resp_exp.json()["data"]
    assert "tool_selections" in exp_data
    assert exp_data["tool_selections"]["jira_step"] == "Selected tool create_issue"
    
    # 9. Hit POST /v1/planner/improve
    resp_imp = client.post(
        "/v1/planner/improve",
        json={"session_id": session_id, "feedback": "Add an extra check step"},
        headers=headers
    )
    assert resp_imp.status_code == 200
    imp_data = resp_imp.json()["data"]
    assert imp_data["workflow_id"] == wf_id
