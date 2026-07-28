import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import json

async def run():
    client = AsyncIOMotorClient("mongodb+srv://syncsphere:SyncSphere123@cluster0.zoo2vpl.mongodb.net/?appName=Cluster0")
    db = client.syncsphere
    
    slacks = await db.slack_tokens.find().to_list(None)
    googles = await db.google_tokens.find().to_list(None)
    states = await db.oauth_states.find().to_list(None)
    
    out = {
        "slack": [{"_id": str(s.get('_id')), "org": s.get('organization_id'), "user": s.get('user_id'), "team": s.get('team_id')} for s in slacks],
        "google": [{"_id": str(g.get('_id')), "org": g.get('organization_id'), "user": g.get('user_id')} for g in googles],
        "state": []
    }
    with open('db_out.json', 'w') as f:
        json.dump(out, f, indent=2)

asyncio.run(run())
