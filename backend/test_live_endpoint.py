import json
import asyncio
import httpx
import time
from syncsphere.identity.infrastructure.jwt_service import JWTService

async def run_live_test():
    jwt_service = JWTService()
    token = jwt_service.create_access_token(
        user_id="sys_admin_123",
        org_id="org_default",
        roles=["Admin"]
    )
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "prompt": "Send a Slack message to #all-janhvi saying 'SyncSphere multi integration test'. Send an email to my test email with subject 'SyncSphere Multi Integration Test' and body 'Multi integration test successful.'. Create a Google Calendar event named 'SyncSphere Multi Integration Test' tomorrow from 2 PM to 3 PM. Add a row to my Google Sheet with the values 'Multi Integration Test', 'Success', and today's date."
    }
    
    output = {}
    async with httpx.AsyncClient() as client:
        t0 = time.time()
        try:
            r = await client.post("http://localhost:8000/v1/tasks/plan-with-ai", headers=headers, json=payload, timeout=120.0)
            t1 = time.time()
            output["time_taken"] = t1 - t0
            output["status_code"] = r.status_code
            try:
                output["response"] = r.json()
            except:
                output["response_text"] = r.text
        except Exception as e:
            t1 = time.time()
            output["time_taken"] = t1 - t0
            output["error"] = str(e)

    with open("test_result.json", "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)

if __name__ == "__main__":
    asyncio.run(run_live_test())
