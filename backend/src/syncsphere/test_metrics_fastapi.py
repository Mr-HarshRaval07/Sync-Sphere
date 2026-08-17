import asyncio
import os
import sys

os.environ["HTTP_PORT"] = "8000"
os.environ["MONGODB_URI"] = "mongodb://localhost:27017"
os.environ["JWKS_URL"] = "http://localhost:8000/.well-known/jwks.json"
os.environ["JWT_AUDIENCE"] = "syncsphere"
os.environ["JWT_ISSUER"] = "syncsphere"

from fastapi.testclient import TestClient
from syncsphere.main import app
from syncsphere.shared_kernel.infrastructure.http.dependencies import get_org_id

def run_test():
    client = TestClient(app)
    
    def override_get_org_id():
        return "org_01HFWJ6VDBP7A5N8G1Q9Z2"
        
    app.dependency_overrides[get_org_id] = override_get_org_id
    
    # We must also mock verify_jwt because plan-with-ai calls `claims = Depends(verify_jwt)`
    from syncsphere.shared_kernel.infrastructure.http.dependencies import verify_jwt
    def override_verify_jwt():
        return {"org": "org_01HFWJ6VDBP7A5N8G1Q9Z2", "sub": "test_user_id"}
    app.dependency_overrides[verify_jwt] = override_verify_jwt
    
    with TestClient(app) as client:
        print("Executing 5 AI Planner requests natively via TestClient...")
        for i in range(5):
            print(f"Request {i+1}/5...")
            plan_resp = client.post("/v1/tasks/plan-with-ai", json={"prompt": f"Set a reminder {i}"})
            if plan_resp.status_code != 200:
                print(f"Error: {plan_resp.text}")
                
        print("\nFetching Dashboard stats...")
        
        dash_resp = client.get("/v1/observability/dashboard")
        if dash_resp.status_code == 200:
            data = dash_resp.json()
            print("--- AI GATEWAY DASHBOARD ---")
            import json
            ai_data = data.get("data", {}).get("ai_gateway", {})
            print(json.dumps(ai_data, indent=2))
            
            tr = ai_data.get("total_requests", 0)
            ti = ai_data.get("input_tokens", 0)
            to = ai_data.get("output_tokens", 0)
            avg = (ti + to) // tr if tr > 0 else 0
            print(f"Calculated Avg Tokens/Req: {avg}")
        else:
            print("Failed to get dashboard:", dash_resp.status_code, dash_resp.text)

run_test()
