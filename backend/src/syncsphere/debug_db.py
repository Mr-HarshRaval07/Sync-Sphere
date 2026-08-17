import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def check():
    client = AsyncIOMotorClient('mongodb://localhost:27017')
    db = client['syncsphere_core']
    col = db['prompt_executions']
    
    docs = await col.find({}, sort=[("_id", -1)]).limit(1).to_list(length=1)
    if not docs:
        print("No documents found in syncsphere_core.prompt_executions")
        return
        
    doc = docs[0]
    print("\n--- MONGODB PROMPTEXECUTION DOCUMENT ---")
    print(f"Provider: {doc.get('provider_name')}")
    print(f"Model: {doc.get('model_id')}")
    print(f"Prompt Tokens: {doc.get('prompt_tokens')}")
    print(f"Completion Tokens: {doc.get('completion_tokens')}")
    print(f"Total Tokens: {doc.get('total_tokens')}")
    print(f"Latency: {doc.get('latency_ms')}")
    print(f"Created at: {doc.get('created_at')}")
    print("----------------------------------------\n")

if __name__ == "__main__":
    asyncio.run(check())
