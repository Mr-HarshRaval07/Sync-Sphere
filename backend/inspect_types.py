import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import json

async def run():
    client = AsyncIOMotorClient("mongodb+srv://syncsphere:SyncSphere123@cluster0.zoo2vpl.mongodb.net/?appName=Cluster0")
    db = client.syncsphere
    
    slacks = await db.slack_tokens.find().to_list(None)
    slack = slacks[0]
    org_type = type(slack['organization_id']).__name__

    with open('db_types.json', 'w') as f:
        json.dump({"slack_org_type": org_type, "slack_org_val": str(slack['organization_id'])}, f)

asyncio.run(run())
