import json
import asyncio
from fastapi.testclient import TestClient
from syncsphere.main import app
from syncsphere.shared_kernel.infrastructure.http.dependencies import verify_jwt

def override_verify_jwt():
    return {"org": "org_123", "sub": "user_123", "role": "Admin"}

app.dependency_overrides[verify_jwt] = override_verify_jwt

payload = {
    "prompt": "Launch a new website on August 15. Create a GitHub issue for the development team, notify my team in Slack, send an email to jayant32@gmail.com with the launch plan, schedule a launch meeting on August 14 at 10 AM, and add the project name, deadline, priority, and status to my Google Sheet."
}

print("Sending POST /v1/tasks/plan-with-ai with overloaded Auth...")
with TestClient(app) as client:
    r = client.post("/v1/tasks/plan-with-ai", json=payload)
    print(f"HTTP Status: {r.status_code}")
    try:
        print(json.dumps(r.json(), indent=2))
    except:
        print(r.text)
