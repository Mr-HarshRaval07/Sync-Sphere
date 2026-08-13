"""Ultra-minimal evidence - just the numbers."""
import asyncio
import sys
import httpx
import json
import os
sys.path.insert(0, "src")

BASE_URL = "http://localhost:8000"

async def main():
    from syncsphere.core.config.settings import settings
    from motor.motor_asyncio import AsyncIOMotorClient
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))
    
    mongo_uri = str(getattr(settings, "mongodb_uri", getattr(settings, "mongo_uri", "")))
    db_name = str(getattr(settings, "mongodb_database", "syncsphere"))
    mc = AsyncIOMotorClient(mongo_uri)
    db = mc[db_name]

    async with httpx.AsyncClient(timeout=120) as hc:
        # Get JWT token via login
        token = "test"
        org_id = "org-default"
        
        r = await hc.post(f"{BASE_URL}/v1/auth/login", json={"email":"admin@syncsphere.ai","password":"admin123"})
        if r.status_code != 200:
            r = await hc.post(f"{BASE_URL}/v1/auth/login", json={"email":"test@syncsphere.ai","password":"password123"})
        if r.status_code == 200:
            d = r.json()
            token = (d.get("data") or {}).get("access_token") or d.get("access_token", "test")
            try:
                import jwt as pyjwt
                pl = pyjwt.decode(token, options={"verify_signature": False})
                org_id = pl.get("org", "org-default")
            except: pass

        sys.stdout.write(f"TOKEN_ORG_ID={org_id}\n")
        sys.stdout.flush()

        # 1) Direct OpenRouter call
        api_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("LLM_API_KEY")
        model = os.getenv("LLM_MODEL", "openai/gpt-4o-mini")
        if api_key:
            r2 = await hc.post("https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json",
                         "HTTP-Referer": "http://localhost:3000", "X-Title": "SyncSphere AI"},
                json={"model": model, "messages": [{"role":"user","content":"reply: ok"}], "max_tokens": 5})
            sys.stdout.write(f"OPENROUTER_STATUS={r2.status_code}\n")
            if r2.status_code == 200:
                u = r2.json().get("usage", {})
                sys.stdout.write(f"OPENROUTER_USAGE={json.dumps(u)}\n")
            sys.stdout.flush()

        # 2) Plan with AI
        r3 = await hc.post(f"{BASE_URL}/v1/tasks/plan-with-ai",
            headers={"Authorization": f"Bearer {token}"},
            json={"prompt": "Create a test task - no integrations"})
        sys.stdout.write(f"PLAN_WITH_AI_STATUS={r3.status_code}\n")
        sys.stdout.flush()
        await asyncio.sleep(2)

        # 3) MongoDB
        agg = await db["prompt_executions"].aggregate([
            {"$match": {"org_id": org_id}},
            {"$group": {"_id": None, "t": {"$sum": "$total_tokens"}, "p": {"$sum": "$prompt_tokens"}, "c": {"$sum": "$completion_tokens"}, "n": {"$sum": 1}}}
        ]).to_list(1)
        if agg:
            a = agg[0]
            sys.stdout.write(f"MONGO_DOCS={a['n']}\nMONGO_TOTAL_TOKENS={a['t']}\nMONGO_PROMPT_TOKENS={a['p']}\nMONGO_COMPLETION_TOKENS={a['c']}\n")
        else:
            sys.stdout.write(f"MONGO_DOCS=0\n")
        sys.stdout.flush()

        # Latest doc
        doc = await db["prompt_executions"].find_one({"org_id": org_id}, sort=[("created_at", -1)])
        if doc:
            sys.stdout.write(f"LATEST_DOC provider={doc.get('provider_name')} model={doc.get('model_id')} prompt_tokens={doc.get('prompt_tokens')} completion_tokens={doc.get('completion_tokens')} total_tokens={doc.get('total_tokens')} latency_ms={doc.get('latency_ms')} created_at={doc.get('created_at')}\n")
        sys.stdout.flush()

        # 4) Dashboard API
        r4 = await hc.get(f"{BASE_URL}/v1/observability/dashboard",
            headers={"Authorization": f"Bearer {token}"})
        sys.stdout.write(f"DASHBOARD_STATUS={r4.status_code}\n")
        if r4.status_code == 200:
            ai = r4.json().get("data", {}).get("ai_gateway", {})
            sys.stdout.write(f"DASHBOARD_JSON={json.dumps(ai)}\n")
            sys.stdout.write(f"DASHBOARD_TOKEN_USAGE={ai.get('token_usage',0)}\n")
            sys.stdout.write(f"DASHBOARD_INPUT={ai.get('input_tokens',0)}\n")
            sys.stdout.write(f"DASHBOARD_OUTPUT={ai.get('output_tokens',0)}\n")
            sys.stdout.write(f"DASHBOARD_REQUESTS={ai.get('total_requests',0)}\n")
            sys.stdout.write(f"DASHBOARD_LAST_REQUEST={ai.get('last_request_at')}\n")
        sys.stdout.flush()

asyncio.run(main())
