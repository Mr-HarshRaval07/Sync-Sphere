import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from syncsphere.core.config.settings import settings
import json
from bson.objectid import ObjectId

class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        return super().default(obj)

async def scan_db():
    client = AsyncIOMotorClient(settings.mongodb_uri)
    db = client[settings.mongodb_database]
    
    collections = await db.list_collection_names()
    results = []
    
    for coll_name in collections:
        coll = db[coll_name]
        try:
            # We are using text search or exact regex search if text index isn't set
            cursor = coll.find({"$or": [
                {"$text": {"$search": "patient"}},
                {"system_template": {"$regex": "patient", "$options": "i"}},
                {"user_template": {"$regex": "patient", "$options": "i"}},
                {"description": {"$regex": "patient", "$options": "i"}},
                {"name": {"$regex": "patient", "$options": "i"}},
                {"title": {"$regex": "patient", "$options": "i"}},
                {"workflow_name": {"$regex": "patient", "$options": "i"}}
            ]}).limit(20)
            
            docs = await cursor.to_list(length=20)
            for d in docs:
                results.append((coll_name, d))
        except Exception as e:
            # Fallback to a broader regex search on common text fields if index fails
            cursor = coll.find({"$or": [
                {"system_template": {"$regex": "patient", "$options": "i"}},
                {"description": {"$regex": "patient", "$options": "i"}},
                {"name": {"$regex": "patient", "$options": "i"}},
                {"content": {"$regex": "patient", "$options": "i"}}
            ]}).limit(10)
            try:
                docs = await cursor.to_list(length=10)
                for d in docs:
                    results.append((coll_name, d))
            except Exception:
                pass
                
    if not results:
        print("No documents containing 'patient' found in explicit fields.")
        prompt_coll = db['PromptTemplateDocument']
        if prompt_coll:
             docs = await prompt_coll.find({}).to_list(length=100)
             for d in docs:
                 s = json.dumps(d, cls=JSONEncoder)
                 if "patient" in s.lower() or "medical" in s.lower():
                     print("FOUND IN prompt_templates:", d.get('name'))
    else:
        for r in results:
            print(f"FOUND IN {r[0]}: {r[1].get('name') or r[1].get('title') or r[1].get('_id')}")

if __name__ == "__main__":
    asyncio.run(scan_db())
