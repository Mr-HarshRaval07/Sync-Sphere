"""Minimal targeted evidence script - prints only what matters."""
import asyncio
import sys
import httpx
import jwt as pyjwt
sys.path.insert(0, "src")

BASE_URL = "http://localhost:8000"

async def main():
    from syncsphere.core.config.settings import settings
    from motor.motor_asyncio import AsyncIOMotorClient
    
    mono_attr = None
    for attr in ["mongodb_uri", "mongo_uri"]:
        v = getattr(settings, attr, None)
        if v:
            mono_attr = str(v); break
    
    db_name = str(getattr(settings, "mongodb_database", "syncsphere"))
    client = AsyncIOMotorClient(mono_attr)
    db = client[db_name]

    async with httpx.AsyncClient(timeout=30) as hc:
        # 1) Try to login
        r = await hc.post(f"{BASE_URL}/v1/auth/login", json={"email":"test@syncsphere.ai","password":"password123"})
        if r.status_code == 200:
            td = r.json()
            token = td.get("data",{}).get("access_token") or td.get("access_token","test")
        else:
            token = "test"
        
        try:
            payload = pyjwt.decode(token, options={"verify_signature": False})
            org_id = payload.get("org","org-default")
        except:
            org_id = "org-default"
        
        print(f"ORG_ID={org_id}")
        
        # 2) MongoDB summary for this org
        agg = await db["prompt_executions"].aggregate([
            {"$match":{"org_id":org_id}},
            {"$group":{"_id":None,"total_tokens":{"$sum":"$total_tokens"},"prompt_tokens":{"$sum":"$prompt_tokens"},"completion_tokens":{"$sum":"$completion_tokens"},"count":{"$sum":1}}}
        ]).to_list(1)
        
        if agg:
            a = agg[0]
            print(f"MONGO_COUNT={a['count']}")
            print(f"MONGO_TOTAL_TOKENS={a['total_tokens']}")
            print(f"MONGO_PROMPT_TOKENS={a['prompt_tokens']}")
            print(f"MONGO_COMPLETION_TOKENS={a['completion_tokens']}")
        else:
            print("MONGO_COUNT=0 (no docs for this org_id)")
        
        # Also show all orgs in DB
        all_agg = await db["prompt_executions"].aggregate([
            {"$group":{"_id":"$org_id","count":{"$sum":1},"total_tokens":{"$sum":"$total_tokens"}}}
        ]).to_list(20)
        print(f"\nALL_ORGS_IN_DB:")
        for a in all_agg:
            print(f"  org={a['_id']} docs={a['count']} total_tokens={a['total_tokens']}")
        
        # 3) Latest 3 documents
        docs = await db["prompt_executions"].find({}).sort("created_at",-1).to_list(3)
        print(f"\nLATEST_3_DOCS:")
        for d in docs:
            print(f"  org={d.get('org_id')} provider={d.get('provider_name')} prompt_tokens={d.get('prompt_tokens')} completion_tokens={d.get('completion_tokens')} total_tokens={d.get('total_tokens')} latency_ms={d.get('latency_ms')} created_at={d.get('created_at')}")
        
        # 4) Dashboard API
        r2 = await hc.get(f"{BASE_URL}/v1/observability/dashboard", headers={"Authorization":f"Bearer {token}"})
        print(f"\nDASHBOARD_STATUS={r2.status_code}")
        if r2.status_code == 200:
            ai = r2.json().get("data",{}).get("ai_gateway",{})
            print(f"DASHBOARD_TOKEN_USAGE={ai.get('token_usage',0)}")
            print(f"DASHBOARD_INPUT_TOKENS={ai.get('input_tokens',0)}")
            print(f"DASHBOARD_OUTPUT_TOKENS={ai.get('output_tokens',0)}")
            print(f"DASHBOARD_TOTAL_REQUESTS={ai.get('total_requests',0)}")
            print(f"DASHBOARD_LAST_REQUEST_AT={ai.get('last_request_at','null')}")

asyncio.run(main())
