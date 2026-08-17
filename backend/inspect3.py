import asyncio, json
import motor.motor_asyncio
import datetime
from bson import ObjectId

class Encoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ObjectId): return str(obj)
        if isinstance(obj, datetime.datetime): return obj.isoformat()
        return json.JSONEncoder.default(self, obj)

async def main():
    client = motor.motor_asyncio.AsyncIOMotorClient("mongodb://root:rootpassword@localhost:27017/syncsphere?authSource=admin")
    db = client["syncsphere"]
    
    tokens = await db.google_tokens.find({}).to_list(None)
    print(f"GOOGLE TOKENS IN DB: {len(tokens)}")
    for t in tokens:
        print(f" - {t.get('google_email')} (org: {t.get('organization_id')})")
        
    print("\n----------------\n")
    
    tasks = await db.tasks.find({}).sort("created_at", -1).limit(3).to_list(None)
    for t in tasks:
        print('TASK:', t.get('title'), '| STATUS:', t.get('status'))
        for a in t.get('automations', []):
            print('  ACTION:', a.get('action'), '| STATUS:', a.get('status'))
            print('  CONFIG:', json.dumps(a.get('config', {})))
            if a.get('error'): print('  ERROR:', a.get('error'))

if __name__ == "__main__":
    asyncio.run(main())
