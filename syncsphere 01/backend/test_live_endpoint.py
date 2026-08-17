import json
import asyncio
import httpx
from syncsphere.identity.infrastructure.jwt_service import JWTService

async def run_live_test():
    jwt_service = JWTService()
    # Generate mock jwt for an organization
    token = jwt_service.create_access_token(
        user_id="sys_admin_123",
        org_id="org_123",
        roles=["Admin"]
    )
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "prompt": "Launch a new website on August 15. Create a GitHub issue for the development team, notify my team in Slack, send an email to jayant32@gmail.com with the launch plan, schedule a launch meeting on August 14 at 10 AM, and add the project name, deadline, priority, and status to my Google Sheet."
    }
    
    async with httpx.AsyncClient() as client:
        print("Sending POST /v1/tasks/plan-with-ai...")
        r = await client.post("http://localhost:8000/v1/tasks/plan-with-ai", headers=headers, json=payload, timeout=60.0)
        print(f"HTTP Status: {r.status_code}")
        try:
            print(json.dumps(r.json(), indent=2))
        except Exception:
            print("Response:", r.text)

if __name__ == "__main__":
    asyncio.run(run_live_test())
