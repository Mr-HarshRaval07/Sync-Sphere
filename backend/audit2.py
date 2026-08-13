import asyncio
import pprint
from syncsphere.core.config.settings import settings
from motor.motor_asyncio import AsyncIOMotorClient

async def main():
    print(f"MongoDB URI: {settings.mongodb_uri}")
    client = AsyncIOMotorClient(settings.mongodb_uri)
    db = client.get_database(settings.mongodb_database)
    
    print("=== WORKFLOW EXECUTIONS ===")
    count = await db.workflow_executions.count_documents({})
    print(f"Total: {count}")
    logs = await db.workflow_executions.find().to_list(5)
    for l in logs:
        print("\nLog Doc:", l.get('_id'))
        print("created_at:", l.get("created_at"))
        print("status:", l.get("status"))
        print("workflow_id:", l.get("workflow_id"))
        print("organization_id:", l.get("organization_id"))
    
    print("\n=== PROMPT EXECUTIONS ===")
    p_count = await db.prompt_executions.count_documents({})
    print(f"Total: {p_count}")

if __name__ == "__main__":
    asyncio.run(main())
