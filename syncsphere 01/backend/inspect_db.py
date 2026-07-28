import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import pprint

async def run():
    client = AsyncIOMotorClient("mongodb+srv://syncsphere:SyncSphere123@cluster0.zoo2vpl.mongodb.net/?appName=Cluster0")
    db = client.syncsphere
    print('--- Slack Tokens ---')
    slacks = await db.slack_tokens.find().to_list(None)
    for s in slacks:
        print(s)
        
    print('\n--- Google Tokens ---')
    googles = await db.google_tokens.find().to_list(None)
    for g in googles:
        print(g)

    print('\n--- GitHub Tokens ---')
    githubs = await db.github_tokens.find().to_list(None)
    for g in githubs:
        print(g)

    print('\n--- OAuth States ---')
    states = await db.oauth_states.find().to_list(None)
    for s in states:
        print(s)

asyncio.run(run())
