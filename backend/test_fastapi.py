import json
import asyncio
from fastapi.testclient import TestClient
from syncsphere.main import app
from syncsphere.shared_kernel.infrastructure.http.dependencies import verify_jwt

def override_verify_jwt():
    return {"org": "org_123", "sub": "user_123", "role": "Admin"}

app.dependency_overrides[verify_jwt] = override_verify_jwt

payload = {
    "prompt": "Send a Slack message to 'my channel' saying 'Invalid channel test'."
}

print("Sending POST /v1/tasks/plan-with-ai with overloaded Auth...")
with TestClient(app) as client:
    r = client.post("/v1/tasks/plan-with-ai", json=payload)
    print(f"HTTP Status: {r.status_code}")
    try:
        print(json.dumps(r.json(), indent=2))
    except:
        print(r.text)
