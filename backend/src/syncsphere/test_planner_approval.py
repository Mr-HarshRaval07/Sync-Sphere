import requests
import time
import json
import uuid

BASE_URL = "http://localhost:8000/v1"
TEST_USER = "admin@acme.ai"
TOKEN = "MOCK_DEVELOPMENT_TOKEN" 

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

def run_test():
    print("1. Planning Workflow with AI...")
    plan_body = {
        "prompt": "Send a priority email to client@example.com confirming project completion."
    }
    r = requests.post(f"{BASE_URL}/tasks/plan-with-ai", json=plan_body, headers=headers)
    
    if r.status_code != 200:
        print(f"Plan failed: {r.status_code} {r.text}")
        return
        
    data = r.json()
    validated_data = data.get("data", {})
    integrations = validated_data.get("integrations", [])
    print(f"Found {len(integrations)} integrations.")
    
    has_approval = False
    has_gmail = False
    for i in integrations:
        print(f" - {i['action']}")
        if "system.approval" in i["action"]:
            has_approval = True
        if "gmail" in i["action"]:
            has_gmail = True
            
    if not (has_approval and has_gmail):
        print("ERROR: Missing approval gate before risky action!")
        return
        
    print("Approval node successfully injected by AI gateway!")
    
    # 2. Confirm Plan
    print("\n2. Confirming plan to create task & start execution...")
    task_req = validated_data["task"]
    body = {
        "tasks": [{
            "title": task_req["title"],
            "description": task_req["description"],
            "assigned_to": task_req["assignee"],
            "priority": task_req["priority"],
            "status": task_req["status"],
            "due_date": task_req["due_date"],
            "automations": integrations
        }]
    }
    
    r = requests.post(f"{BASE_URL}/tasks/confirm-plan", json=body, headers=headers)
    if r.status_code != 201:
        print(f"Confirm failed: {r.status_code} {r.text}")
        return
        
    tasks = r.json()["data"]
    task_id = tasks[0]["id"]
    print(f"Task created: {task_id}")
    
    # Wait for execution engine to pause
    print("Waiting 3 seconds for execution engine to halt at approval gate...")
    time.sleep(3)
    
    print("\n3. Verifying Approvals Dashboard API Returns Pending Request...")
    r = requests.get(f"{BASE_URL}/approvals", headers=headers)
    if r.status_code != 200:
        print(f"Approvals failed: {r.status_code} {r.text}")
        return
        
    approvals = r.json().get("data", [])
    pending_appr = next((a for a in approvals if a["workflow_id"] == task_id and a["status"] == "pending"), None)
    
    if not pending_appr:
        print("ERROR: No pending approval request created in MongoDB!")
        return
        
    appr_id = pending_appr["id"]
    print(f"Success! Approval Request {appr_id} created and waiting for decision.")
    
    # Check task execution status
    r = requests.get(f"{BASE_URL}/tasks/{task_id}", headers=headers)
    t_data = r.json().get("data", {})
    auto_status = [a["status"] for a in t_data.get("automations", [])]
    print(f"Current Automation Status Sequence: {auto_status}")
    if "awaiting_approval" not in auto_status:
        print("ERROR: Task did not persist 'awaiting_approval' status natively.")
        return
        
    # 4. Approve!
    print(f"\n4. Submitting APPROVAL grant for {appr_id}...")
    r = requests.post(f"{BASE_URL}/approvals/{appr_id}/approve", json={"comment": "LGTM"}, headers=headers)
    if r.status_code != 200:
        print(f"Approve request failed: {r.status_code} {r.text}")
        return
        
    print("Waiting 2 seconds for execution to resume natively...")
    time.sleep(2)
    
    # Verify execution resumed
    r = requests.get(f"{BASE_URL}/tasks/{task_id}", headers=headers)
    t_data = r.json().get("data", {})
    auto_status = [a["status"] for a in t_data.get("automations", [])]
    print(f"Final Automation Status Sequence: {auto_status}")
    
    if "awaiting_approval" in auto_status:
        print("ERROR: Execution DID NOT resume after approval was granted!")
        return
        
    print("END-TO-END VALIDATION COMPLETED SUCCESSFULLY. The Execution engine correctly halted and resumed upon granting standard approvals.")

if __name__ == "__main__":
    run_test()
