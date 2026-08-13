import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def check_mongo():
    client = AsyncIOMotorClient('mongodb://localhost:27017')
    db = client['syncsphere_core']
    col = db['prompt_executions']
    
    docs = await col.find({}, sort=[('_id', -1)]).limit(5).to_list(length=5)
    if not docs:
        print('No executions found in mongo.')
    for d in docs:
        print(f"ID: {d.get('_id')}")
        print(f"Provider: {d.get('provider_name')}")
        print(f"Model: {d.get('model_id')}")
        print(f"Prompt: {d.get('prompt_tokens')}")
        print(f"Completion: {d.get('completion_tokens')}")
        print(f"Total: {d.get('total_tokens')}")
        print('-'*20)

asyncio.run(check_mongo())
