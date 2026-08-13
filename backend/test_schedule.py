import asyncio
import httpx
from syncsphere.tasks.schemas import PlanWithAIRequest

async def main():
    async with httpx.AsyncClient(timeout=30.0) as client:
        # First login
        res = await client.post("http://localhost:8000/v1/auth/login", json={
            "email": "demo@syncsphere.ai",
            "password": "Password123!"
        })
        if res.status_code != 200:
            print("Login failed:", res.text)
            return

        token = res.json()["data"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test creating a schedule
        res2 = await client.post("http://localhost:8000/v1/schedules", headers=headers, json={
            "workflow_id": "000000000000000000000000",
            "schedule_type": "daily"
        })
        print("Create schedule:", res2.status_code, res2.text)

if __name__ == "__main__":
    asyncio.run(main())
