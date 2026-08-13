import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def main():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client["syncsphere"]
    collnames = await db.list_collection_names()
    
    with open("audit_out.txt", "w", encoding="utf-8") as f:
        f.write(f"Collections ({len(collnames)}):\n")
        for x in collnames:
            f.write(x + "\n")
            
if __name__ == "__main__":
    asyncio.run(main())
