"""Deep MongoDB diagnostic - shows all details"""
import asyncio
import sys
import warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, "src")

async def check():
    from syncsphere.core.config.settings import settings
    from motor.motor_asyncio import AsyncIOMotorClient
    
    mongo_uri = None
    for attr in ["mongodb_uri", "mongo_uri", "MONGODB_URI"]:
        val = getattr(settings, attr, None)
        if val:
            mongo_uri = str(val)
            break
    if not mongo_uri:
        for attr in dir(settings):
            sub = getattr(settings, attr, None)
            if sub and hasattr(sub, "uri"):
                mongo_uri = str(sub.uri)
                break
    
    db_name = None
    for attr in ["mongodb_database", "mongo_database", "MONGODB_DATABASE"]:
        val = getattr(settings, attr, None)
        if val:
            db_name = str(val)
            break
    if not db_name:
        db_name = "syncsphere"
    
    print(f"DB: {db_name}")
    
    client = AsyncIOMotorClient(mongo_uri)
    db = client[db_name]
    
    # Get all prompt_executions
    docs = await db["prompt_executions"].find({}).to_list(10)
    print(f"\nprompt_executions docs: {len(docs)}")
    for d in docs:
        print("---")
        print(f"  _id: {d.get('_id')}")
        print(f"  org_id: {d.get('org_id')}")
        print(f"  provider_name: {d.get('provider_name')}")
        print(f"  model_id: {d.get('model_id')}")
        print(f"  prompt_tokens: {d.get('prompt_tokens')}")
        print(f"  completion_tokens: {d.get('completion_tokens')}")
        print(f"  total_tokens: {d.get('total_tokens')}")
        print(f"  latency_ms: {d.get('latency_ms')}")
        print(f"  created_at: {d.get('created_at')}")
    
    # Get users to compare org_id
    print("\n=== users ===")
    users = await db["users"].find({}).to_list(3)
    for u in users:
        print(f"  user email={u.get('email')} org_id={u.get('organization_id')}")
    
    # Get orgs
    print("\n=== organizations ===")
    orgs = await db["organizations"].find({}).to_list(3)
    for o in orgs:
        oid = str(o.get("_id", ""))
        print(f"  org _id={oid} name={o.get('name')}")
    
    # Now simulate what analytics does: find docs per org
    print("\n=== Analytics simulation ===")
    if users:
        org_id_from_user = str(users[0].get("organization_id", ""))
        print(f"Querying with org_id from user: {org_id_from_user}")
        count = await db["prompt_executions"].count_documents({"org_id": org_id_from_user})
        print(f"  prompt_executions for that org_id: {count}")
    
    if docs:
        doc_org_id = docs[0].get("org_id", "")
        print(f"\nQuerying with org_id from doc: {doc_org_id}")
        count2 = await db["prompt_executions"].count_documents({"org_id": doc_org_id})
        print(f"  prompt_executions count: {count2}")

asyncio.run(check())
