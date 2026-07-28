from fastapi.testclient import TestClient
from syncsphere.main import app

client = TestClient(app)

def test_liveness_check():
    """Tests /v1/health/live liveness probe endpoint."""
    response = client.get("/v1/health/live")
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["status"] == "alive"
    assert "request_id" in data["meta"]

def test_health_check():
    """Tests /v1/health basic check endpoint."""
    response = client.get("/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["status"] == "healthy"
    assert "timestamp" in data["data"]
    assert "request_id" in data["meta"]

def test_readiness_check():
    """
    Tests /v1/health/ready readiness check endpoint.
    Since DB/Redis managers are not connected in testing without fixtures,
    we verify it responds (either ready or degraded depending on local docker context).
    """
    response = client.get("/v1/health/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["status"] in ("ready", "degraded")
    assert "checks" in data["data"]
