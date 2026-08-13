"""Quick MongoDB diagnostic"""
import asyncio
import sys
import warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, "src")

async def check():
    from syncsphere.core.config.settings import settings
    from motor.motor_asyncio import AsyncIOMotorClient
    
    # Find mongo settings
    for attr in ["mongodb_uri", "mongo_uri", "MONGODB_URI"]:
        val = getattr(settings, attr, None)
        if val:
            mongo_uri = str(val)
            print(f"Found URI at settings.{attr}: {mongo_uri[:40]}...")
            break
    else:
        # Try nested
        for attr in dir(settings):
            sub = getattr(settings, attr, None)
            if sub and hasattr(sub, "uri"):
                mongo_uri = str(sub.uri)
                print(f"Found URI at settings.{attr}.uri")
                break
        else:
            print("ERROR: Cannot find MongoDB URI in settings")
            return
    
    for attr in ["mongodb_database", "mongo_database", "MONGODB_DATABASE"]:
        val = getattr(settings, attr, None)
        if val:
            db_name = str(val)
            print(f"Found DB at settings.{attr}: {db_name}")
            break
    else:
        db_name = "syncsphere"
        print(f"Using default db_name: {db_name}")
    
    client = AsyncIOMotorClient(mongo_uri)
    db = client[db_name]
    
    colls = await db.list_collection_names()
    print(f"\nCollections: {colls}")
    
    pe_count = await db["prompt_executions"].count_documents({})
    print(f"\nprompt_executions count: {pe_count}")
    
    if pe_count > 0:
        docs = await db["prompt_executions"].find({}).to_list(5)
        for d in docs:
            print(f"  id={d['_id']} org={d.get('org_id')} total_tokens={d.get('total_tokens')} prompt_tokens={d.get('prompt_tokens')} provider={d.get('provider_name')}")
    else:
        print("  NO documents in prompt_executions collection!")
    
    # Check orgs
    org_count = await db["organizations"].count_documents({})
    print(f"\norganizations count: {org_count}")
    if org_count > 0:
        orgs = await db["organizations"].find({}).to_list(3)
        for o in orgs:
            print(f"  org: id={o.get('_id')} name={o.get('name')}")
    
    # Check users for org_id
    user = await db["users"].find_one({})
    if user:
        print(f"\nSample user org_id: {user.get('organization_id')}")
        print(f"Sample user email: {user.get('email')}")
    
    # Check backend logs for any errors related to execution save
    print("\n=== Checking ai_executions / any similar collections ===")
    for coll_name in colls:
        if "exec" in coll_name.lower() or "prompt" in coll_name.lower() or "ai_" in coll_name.lower():
            c = await db[coll_name].count_documents({})
            print(f"  {coll_name}: {c} documents")

asyncio.run(check())
