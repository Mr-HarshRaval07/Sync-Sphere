import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

async def fetch_db():
    client = AsyncIOMotorClient("mongodb+srv://syncsphere:SyncSphere123@cluster0.zoo2vpl.mongodb.net/syncsphere?appName=Cluster0")
    db = client.get_default_database()
    
    # find latest task with Gmail
    cursor = db["tasks"].find({"automations.action": "gmail.send_email"}).sort("created_at", -1).limit(1)
    async for task in cursor:
        import pprint
        pprint.pprint(task)

asyncio.run(fetch_db())
