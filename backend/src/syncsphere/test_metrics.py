import requests
import time
import json

def run():
    print("Logging in...")
    resp = requests.post("http://localhost:8000/v1/auth/login", json={"email": "demo@syncsphere.com", "password": "password"})
    
    if resp.status_code != 200:
        print(f"Login failed: {resp.status_code} - {resp.text}")
        return
        
    token = resp.json().get("data", {}).get("access_token")
    headers = {"Authorization": f"Bearer {token}"}
    
    print("Executing 5 AI Planner requests...")
    for i in range(5):
        print(f"Request {i+1}/5...")
        plan_resp = requests.post("http://localhost:8000/v1/tasks/plan-with-ai", headers=headers, json={"goal": f"Set a reminder {i}"})
        if plan_resp.status_code != 200:
            print(f"Error: {plan_resp.text}")
        time.sleep(1)
        
    print("\nFetching Dashboard stats...")
    dash_resp = requests.get("http://localhost:8000/v1/observability/dashboard", headers=headers)
    if dash_resp.status_code == 200:
        data = dash_resp.json()
        print("--- AI GATEWAY OVERVIEW ---")
        print(json.dumps(data.get("ai_gateway"), indent=2))
        
        # Calculate exactly as frontend does
        stats = data.get("ai_gateway", {})
        tr = stats.get("total_requests", 0)
        ti = stats.get("input_tokens", 0)
        to = stats.get("output_tokens", 0)
        avg = (ti + to) // tr if tr > 0 else 0
        print(f"Calculated Avg Tokens/Req: {avg}")
    else:
        print("Failed to get dashboard:", dash_resp.text)

run()
