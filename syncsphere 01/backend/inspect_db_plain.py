import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import json

async def run():
    client = AsyncIOMotorClient("mongodb+srv://syncsphere:SyncSphere123@cluster0.zoo2vpl.mongodb.net/?appName=Cluster0")
    db = client.syncsphere
    
    slacks = await db.slack_tokens.find().to_list(None)
    for s in slacks:
        print(f"SLACK: _id={s.get('_id')}, org={s.get('organization_id')}, user={s.get('user_id')}, team={s.get('team_id')}")

    googles = await db.google_tokens.find().to_list(None)
    for g in googles:
        print(f"GOOGLE: _id={g.get('_id')}, org={g.get('organization_id')}, user={g.get('user_id')}, email={g.get('google_email')}")

    states = await db.oauth_states.find().to_list(None)
    for s in states:
        print(f"STATE: provider={s.get('provider')}, org={s.get('organization_id')}, user={s.get('user_id')}")

asyncio.run(run())
