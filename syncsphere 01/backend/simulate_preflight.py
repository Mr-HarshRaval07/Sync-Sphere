import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import httpx

async def run():
    client = AsyncIOMotorClient("mongodb+srv://syncsphere:SyncSphere123@cluster0.zoo2vpl.mongodb.net/?appName=Cluster0")
    db = client.syncsphere
    
    # 1. ensure a test token exists
    await db.slack_tokens.update_one(
        {"team_id": "TEST_TEAM"},
        {"$set": {
            "organization_id": "org-default",
            "access_token": "test_token",
            "team_name": "Test Team"
        }},
        upsert=True
    )
    
    # 2. Call confirm-plan using 'test' token
    payload = {
        "tasks": [{
            "title": "Test",
            "description": "Test",
            "priority": "Medium",
            "status": "Pending",
            "automations": [{
                "action": "slack.send_message",
                "config": {"message": "hello"}
            }]
        }]
    }
    
    async with httpx.AsyncClient() as c:
        resp = await c.post(
            "http://localhost:8000/v1/tasks/confirm-plan",
            json=payload,
            headers={"Authorization": "Bearer test"}
        )
        print("STATUS:", resp.status_code)
        print("BODY:", resp.text)

asyncio.run(run())
