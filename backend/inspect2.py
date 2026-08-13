import asyncio, json
import motor.motor_asyncio

async def main():
    client = motor.motor_asyncio.AsyncIOMotorClient("mongodb://localhost:27017")
    db = client["syncsphere_dev"]
    
    tasks = await db.tasks.find({}).sort("created_at", -1).limit(3).to_list(None)
    for t in tasks:
        print('TASK:', t.get('title'), '| STATUS:', t.get('status'))
        for a in t.get('automations', []):
            print('  ACTION:', a.get('action'), '| STATUS:', a.get('status'))
            print('  CONFIG:', json.dumps(a.get('config', {})))

if __name__ == "__main__":
    asyncio.run(main())
