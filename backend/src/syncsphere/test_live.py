import requests
import json
import time

def run():
    print("Executing 5 AI Planner requests natively against LIVE server (No Auth)...")
    for i in range(5):
        print(f"Request {i+1}/5...")
        plan_resp = requests.post("http://localhost:8000/v1/tasks/plan-with-ai", json={"prompt": f"Set a reminder {i}"})
        if plan_resp.status_code != 200:
            print(f"Error: {plan_resp.text}")
        time.sleep(1)
            
    print("\nFetching Dashboard stats...")
    
    dash_resp = requests.get("http://localhost:8000/v1/observability/dashboard")
    if dash_resp.status_code == 200:
        data = dash_resp.json()
        print("--- AI GATEWAY DASHBOARD ---")
        ai_data = data.get("data", {}).get("ai_gateway", {})
        print(json.dumps(ai_data, indent=2))
        
        tr = ai_data.get("total_requests", 0)
        ti = ai_data.get("input_tokens", 0)
        to = ai_data.get("output_tokens", 0)
        avg = (ti + to) // tr if tr > 0 else 0
        print(f"Calculated Avg Tokens/Req: {avg}")
    else:
        print("Failed to get dashboard:", dash_resp.status_code, dash_resp.text)

run()
