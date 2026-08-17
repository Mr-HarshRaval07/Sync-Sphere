import asyncio, sys, json

async def main():
    import motor.motor_asyncio
    client = motor.motor_asyncio.AsyncIOMotorClient("mongodb://localhost:27017")
    db = client["syncsphere_dev"]
    
    # 1. Let's see what Google Tokens exist in the real database!
    tokens = await db.google_tokens.find({}).to_list(None)
    print(f"GOOGLE TOKENS IN DB: {len(tokens)}")
    for t in tokens:
        print(f" - {t.get('google_email')} (org: {t.get('organization_id')})")
        
    print("\n----------------\n")
    
    # 2. Let's see the most recent Task Document's automations to see what the user ACTUALLY triggered!
    tasks = await db.tasks.find({}).sort("created_at", -1).limit(3).to_list(None)
    for task in tasks:
        print(f"TASK: {task.get('title')} (Status: {task.get('status')})")
        for auto in task.get("automations", []):
            print(f"  ACTION: {auto.get('action')} - STATUS: {auto.get('status')}")
            print(f"  CONFIG: {json.dumps(auto.get('config', {}))}")
            if auto.get('error'):
                print(f"  ERROR: {auto.get('error')}")
            if auto.get('result'):
                print(f"  RESULT: {auto.get('result')}")
        print("---\n")

if __name__ == "__main__":
    asyncio.run(main())
