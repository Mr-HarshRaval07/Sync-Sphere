import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def main():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client["syncsphere"]
    
    count_e = await db["executions"].count_documents({})
    print(f"Total executions: {count_e}")
    
    count_er = await db["execution_runs"].count_documents({})
    print(f"Total execution_runs: {count_er}")
            
if __name__ == "__main__":
    asyncio.run(main())
