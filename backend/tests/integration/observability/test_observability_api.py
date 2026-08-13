import pytest
from fastapi.testclient import TestClient
from syncsphere.main import app
from syncsphere.core.dependency_injection.container import container
import asyncio
from datetime import datetime
from unittest.mock import patch, MagicMock, AsyncMock

client = TestClient(app)

@patch("syncsphere.observability.presentation.routes.observability_routes.container.observability_service.dashboard_pipeline.compile_dashboard", new_callable=AsyncMock)
def test_observability_api_flow(mock_compile):
    mock_compile.return_value = {
        "health": {"services": [], "overall_status": "HEALTHY"}, 
        "ai_gateway": {}
    }
    """
    Integration test verifying all presentation routes for observability module:
    1. POST /v1/observability/alerts -> Create alert
    2. GET /v1/observability/alerts -> Retrieve list of alerts
    3. POST /v1/observability/replay -> Start replay
    4. GET /v1/observability/replay/{id} -> Retrieve replay events timeline
    5. GET /v1/observability/traces -> List traces
    6. GET /v1/observability/traces/{id} -> Get trace details
    7. GET /v1/observability/metrics -> Get metric series
    8. GET /v1/observability/metrics/prometheus -> Prometheus metrics export
    9. GET /v1/observability/dashboard -> Compile organization dashboard
    10. GET /v1/observability/health -> Compile service health report
    """
    # 1. Login user to get JWT token
    register_payload = {
        "email": "observability_admin@acme.ai",
        "password": "supersecretpassword123!",
        "first_name": "Observability",
        "last_name": "Tester",
        "org_name": "Acme Observability",
        "org_slug": "acme-observability"
    }
    client.post("/v1/auth/register", json=register_payload)
    
    resp_login = client.post("/v1/auth/login", json={"email": "observability_admin@acme.ai", "password": "supersecretpassword123!"})
    login_data = resp_login.json()["data"]
    access_token = login_data["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    # Retrieve user and org info
    async def get_org_info():
        u = await container.user_repo.get_by_email("observability_admin@acme.ai")
        return u.org_id
    
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    org_id = loop.run_until_complete(get_org_info())

    # --- 1. POST /v1/observability/alerts -> Create Alert ---
    alert_payload = {
        "name": "Database CPU Peak",
        "message": "Database CPU has breached critical 95% threshold.",
        "severity": "CRITICAL",
        "metric_name": "system.cpu_utilization"
    }
    resp = client.post("/v1/observability/alerts", json=alert_payload, headers=headers)
    assert resp.status_code == 200
    alert_data = resp.json()["data"]
    alert_id = alert_data["alert_id"]
    assert alert_id is not None

    # --- 2. GET /v1/observability/alerts -> Retrieve Alerts ---
    resp = client.get("/v1/observability/alerts", headers=headers)
    assert resp.status_code == 200
    alerts_list = resp.json()["data"]
    assert len(alerts_list) >= 1
    assert alerts_list[0]["severity"] == "CRITICAL"

    # --- 3. POST /v1/observability/replay -> Start Replay ---
    replay_payload = {
        "session_id": "session-test-uuid",
        "replay_type": "execution"
    }
    resp = client.post("/v1/observability/replay", json=replay_payload, headers=headers)
    assert resp.status_code == 200
    replay_data = resp.json()["data"]
    assert replay_data["session_id"] == "session-test-uuid"

    # --- 4. GET /v1/observability/replay/{id} -> Get Replay Timeline ---
    resp = client.get("/v1/observability/replay/session-test-uuid?type=execution", headers=headers)
    assert resp.status_code == 200
    replay_details = resp.json()["data"]
    assert replay_details["session_id"] == "session-test-uuid"

    # --- 5 & 6. Distributed Tracing APIs ---
    # Trigger a mock trace/span creation in database to test GETs
    async def create_mock_trace():
        await container.observability_tracer.start_span(
            org_id=org_id,
            name="mock_span_api",
            correlation_id="corr-api-trace-123",
            attributes={"client": "fastapi_test"}
        )
    loop.run_until_complete(create_mock_trace())

    resp = client.get("/v1/observability/traces", headers=headers)
    assert resp.status_code == 200
    traces = resp.json()["data"]
    assert len(traces) >= 1

    resp = client.get("/v1/observability/traces/corr-api-trace-123", headers=headers)
    assert resp.status_code == 200
    trace_details = resp.json()["data"]
    assert trace_details["trace_id"] == "corr-api-trace-123"
    assert len(trace_details["spans"]) >= 1

    # --- 7 & 8. Metrics Dashboard and Prometheus Exporter ---
    # Save a mock metric series
    async def create_mock_metric():
        from syncsphere.observability.domain.value_objects import Metric
        m = Metric(name="system.memory_usage", value=80.0, timestamp=datetime.utcnow())
        await container.observability_metrics_collector.record(org_id, m)
    loop.run_until_complete(create_mock_metric())

    resp = client.get("/v1/observability/metrics?metric_name=system.memory_usage", headers=headers)
    assert resp.status_code == 200
    metric_dash = resp.json()["data"]
    assert metric_dash["metric_name"] == "system.memory_usage"
    assert len(metric_dash["data_points"]) >= 1

    resp = client.get("/v1/observability/metrics/prometheus", headers=headers)
    assert resp.status_code == 200
    assert "system_memory_usage" in resp.text

    # --- 9 & 10. Dashboards and Service Health ---
    resp = client.get("/v1/observability/dashboard", headers=headers)
    assert resp.status_code == 200
    dashboard = resp.json()["data"]
    assert "health" in dashboard
    assert "ai_gateway" in dashboard

    resp = client.get("/v1/observability/health", headers=headers)
    assert resp.status_code == 200
    health = resp.json()["data"]
    assert "services" in health
    assert health["overall_status"] == "HEALTHY"

def test_observability_websocket_connection():
    # Test WebSocket connection path
    # Register/Login
    register_payload = {
        "email": "observability_admin_ws@acme.ai",
        "password": "supersecretpassword123!",
        "first_name": "Observability",
        "last_name": "Tester",
        "org_name": "Acme Observability WS",
        "org_slug": "acme-observability-ws"
    }
    client.post("/v1/auth/register", json=register_payload)

    resp_login = client.post("/v1/auth/login", json={"email": "observability_admin_ws@acme.ai", "password": "supersecretpassword123!"})
    login_data = resp_login.json()["data"]
    access_token = login_data["access_token"]

    async def get_org_info():
        u = await container.user_repo.get_by_email("observability_admin_ws@acme.ai")
        return u.org_id
    
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    org_id = loop.run_until_complete(get_org_info())

    with client.websocket_connect(f"/v1/observability/live?org_id={org_id}") as websocket:
        # Send heartbeat / request text
        websocket.send_text("ping")
        # Hub connection will keep active websocket in memory
