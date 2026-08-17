import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def check():
    client = AsyncIOMotorClient('mongodb://localhost:27017')
    dbs = await client.list_database_names()
    print('Databases:', dbs)
    for d_name in dbs:
        db = client[d_name]
        cols = await db.list_collection_names()
        if 'prompt_executions' in cols:
            print(f'Found prompt_executions in DB: {d_name}')
            col = db['prompt_executions']
            docs = await col.find({}).sort("_id", -1).limit(1).to_list(length=1)
            for doc in docs:
                print('--- MONGODB PROMPTEXECUTION DOCUMENT ---')
                print(f"Provider: {doc.get('provider_name')}")
                print(f"Model: {doc.get('model_id')}")
                print(f"Prompt Tokens: {doc.get('prompt_tokens')}")
                print(f"Completion Tokens: {doc.get('completion_tokens')}")
                print(f"Total Tokens: {doc.get('total_tokens')}")
                print(f"Latency: {doc.get('latency_ms')}")
                import json
                print(json.dumps(doc, default=str, indent=2))
                
asyncio.run(check())
