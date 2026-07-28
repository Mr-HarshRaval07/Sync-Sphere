import pytest
from fastapi.testclient import TestClient
from syncsphere.main import app

client = TestClient(app)

def test_connector_full_api_lifecycle_flow():
    """Tests the full API connector journey: register, verify tools, rotate secrets, invoke tool, delete."""
    
    # 1. Login user to get JWT Admin token
    # (Since conftest wipes stubs before each test, we register a fresh organization admin)
    register_payload = {
        "email": "admin3@acme.ai",
        "password": "supersecretpassword123!",
        "first_name": "Bob",
        "last_name": "Miller",
        "org_name": "Acme Corp 3",
        "org_slug": "acme-corp-3"
    }
    client.post("/v1/auth/register", json=register_payload)
    
    resp_login = client.post("/v1/auth/login", json={"email": "admin3@acme.ai", "password": "supersecretpassword123!"})
    access_token = resp_login.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    # 2. Register Connector (will invoke mock sync capabilities via conftest mocks)
    # The name must be "slack", which matches the mock server tool advertising
    connector_payload = {
        "name": "slack",
        "transport_type": "sse",
        "connection_config": {"url": "http://localhost:8080/sse/slack"},
        "max_requests_per_minute": 100,
        "required_scopes": ["slack:write"]
    }
    resp_reg = client.post("/v1/connectors", json=connector_payload, headers=headers)
    assert resp_reg.status_code == 201
    conn_data = resp_reg.json()["data"]
    conn_id = conn_data["id"]
    assert conn_data["name"] == "slack"
    assert conn_data["status"] == "ENABLED"
    assert conn_data["health"]["status"] == "ONLINE"
    
    # Verify Slack tools are synchronized
    assert len(conn_data["tools"]) == 1
    assert conn_data["tools"][0]["name"] == "slack_post_message"

    # 3. Configure credentials
    cred_payload = {
        "secrets": {"SLACK_BOT_TOKEN": "xoxb-mock-token-value"}
    }
    resp_cred = client.post(f"/v1/connectors/{conn_id}/credentials", json=cred_payload, headers=headers)
    assert resp_cred.status_code == 200
    assert resp_cred.json()["data"]["status"] == "credentials_updated"

    # 4. Invoke MCP Tool call
    call_payload = {
        "tool_name": "slack_post_message",
        "arguments": {"channel": "#all-janhvi", "message": "Hello from SyncSphere AI!"}
    }
    resp_call = client.post(f"/v1/connectors/{conn_id}/tools/slack_post_message/call", json=call_payload, headers=headers)
    assert resp_call.status_code == 200
    call_res = resp_call.json()["data"]
    assert call_res["is_error"] is False
    assert "slack_post_message" in call_res["content"][0]["text"]

    # 5. Delete Connector
    resp_del = client.delete(f"/v1/connectors/{conn_id}", headers=headers)
    assert resp_del.status_code == 204

    # Verify connector is deleted
    resp_get = client.get(f"/v1/connectors/{conn_id}", headers=headers)
    assert resp_get.status_code == 404
