import asyncio
import pprint
from motor.motor_asyncio import AsyncIOMotorClient

async def main():
    client = AsyncIOMotorClient("mongodb://sync_user:development_secret_password_123@localhost:27017/syncsphere?authSource=admin")
    db = client.syncsphere
    
    print("=== WORKFLOW EXECUTIONS ===")
    count = await db.workflow_executions.count_documents({})
    print(f"Total: {count}")
    logs = await db.workflow_executions.find().to_list(2)
    pprint.pprint(logs)
    
    print("\n=== PROMPT EXECUTIONS ===")
    p_count = await db.prompt_executions.count_documents({})
    print(f"Total: {p_count}")
    
    print("\n=== WORKFLOWS ===")
    w_count = await db.workflows.count_documents({})
    print(f"Total: {w_count}")

if __name__ == "__main__":
    asyncio.run(main())
