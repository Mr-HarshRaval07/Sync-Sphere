"""
Live end-to-end telemetry test.
Steps:
1. Login to get a real JWT token
2. Make a plan-with-ai request
3. Check MongoDB for the resulting PromptExecutionDocument
4. Call /observability/dashboard to check token values
"""
import asyncio
import httpx
import json
import sys
sys.path.insert(0, "src")

BASE_URL = "http://localhost:8000"

async def get_token():
    """Try to get a real JWT by logging in."""
    async with httpx.AsyncClient(timeout=30) as client:
        # Try login
        try:
            resp = await client.post(f"{BASE_URL}/v1/auth/login", json={"email": "test@syncsphere.ai", "password": "password123"})
            if resp.status_code == 200:
                data = resp.json()
                token = data.get("data", {}).get("access_token") or data.get("access_token")
                if token:
                    print(f"[OK] Got real JWT token from /auth/login")
                    return token
        except Exception as e:
            print(f"[INFO] Login via /auth/login failed: {e}")

        # Try /auth/token
        try:
            resp = await client.post(f"{BASE_URL}/v1/auth/token", data={"username": "test@syncsphere.ai", "password": "password123"})
            if resp.status_code == 200:
                data = resp.json()
                token = data.get("access_token")
                if token:
                    print(f"[OK] Got real JWT token from /auth/token")
                    return token
        except Exception as e:
            print(f"[INFO] Login via /auth/token failed: {e}")

        # Use test token as fallback
        print("[INFO] Using test token (will map to org-default)")
        return "test"


async def make_plan_request(token: str):
    """Send a plan-with-ai request and return the response."""
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"prompt": "Create a task called 'Telemetry Audit Test' - no integrations needed"}
    
    async with httpx.AsyncClient(timeout=120) as client:
        print(f"\n[INFO] Sending plan-with-ai request...")
        resp = await client.post(f"{BASE_URL}/v1/tasks/plan-with-ai", headers=headers, json=payload)
        print(f"[INFO] HTTP Status: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            print(f"[OK] Plan returned successfully")
            return data
        else:
            print(f"[ERROR] Response: {resp.text[:500]}")
            return None


async def check_mongodb_docs(org_id: str):
    """Check the most recent PromptExecutionDocuments."""
    from syncsphere.core.config.settings import settings
    from motor.motor_asyncio import AsyncIOMotorClient
    
    mongo_uri = None
    for attr in ["mongodb_uri", "mongo_uri"]:
        val = getattr(settings, attr, None)
        if val:
            mongo_uri = str(val)
            break
    
    db_name = getattr(settings, "mongodb_database", "syncsphere")
    
    client = AsyncIOMotorClient(mongo_uri)
    db = client[str(db_name)]
    
    # Get recent docs
    recent = await db["prompt_executions"].find({}).sort("created_at", -1).to_list(3)
    print(f"\n[MONGODB] Most recent PromptExecutionDocuments (total all orgs):")
    for doc in recent:
        print(f"  ---")
        print(f"  _id: {doc.get('_id')}")
        print(f"  org_id: {doc.get('org_id')}")
        print(f"  provider_name: {doc.get('provider_name')}")
        print(f"  model_id: {doc.get('model_id')}")
        print(f"  prompt_tokens: {doc.get('prompt_tokens')}")
        print(f"  completion_tokens: {doc.get('completion_tokens')}")
        print(f"  total_tokens: {doc.get('total_tokens')}")
        print(f"  latency_ms: {doc.get('latency_ms')}")
        print(f"  created_at: {doc.get('created_at')}")
    
    # Check by org_id
    count_for_org = await db["prompt_executions"].count_documents({"org_id": org_id})
    print(f"\n[MONGODB] Docs for org_id='{org_id}': {count_for_org}")
    
    # Sum tokens for this org
    pipeline = [
        {"$match": {"org_id": org_id}},
        {"$group": {
            "_id": None,
            "total_tokens_sum": {"$sum": "$total_tokens"},
            "prompt_tokens_sum": {"$sum": "$prompt_tokens"},
            "completion_tokens_sum": {"$sum": "$completion_tokens"},
            "count": {"$sum": 1}
        }}
    ]
    agg = await db["prompt_executions"].aggregate(pipeline).to_list(1)
    if agg:
        print(f"[MONGODB] Token sums for org '{org_id}':")
        print(f"  total_tokens: {agg[0].get('total_tokens_sum')}")
        print(f"  prompt_tokens: {agg[0].get('prompt_tokens_sum')}")
        print(f"  completion_tokens: {agg[0].get('completion_tokens_sum')}")
        print(f"  doc_count: {agg[0].get('count')}")
    else:
        print(f"[WARNING] No docs for org '{org_id}' - org_id mismatch likely!")
    
    return recent


async def check_dashboard_api(token: str):
    """Call the dashboard API endpoint."""
    headers = {"Authorization": f"Bearer {token}"}
    
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(f"{BASE_URL}/v1/observability/dashboard", headers=headers)
        print(f"\n[DASHBOARD API] Status: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            ai_data = data.get("data", {}).get("ai_gateway", {})
            print(f"[DASHBOARD API] ai_gateway section:")
            print(json.dumps(ai_data, indent=2, default=str))
            
            token_usage = ai_data.get("token_usage", 0)
            input_tokens = ai_data.get("input_tokens", 0)
            output_tokens = ai_data.get("output_tokens", 0)
            total_requests = ai_data.get("total_requests", 0)
            
            print(f"\n[DASHBOARD] token_usage={token_usage}")
            print(f"[DASHBOARD] input_tokens={input_tokens}")
            print(f"[DASHBOARD] output_tokens={output_tokens}")
            print(f"[DASHBOARD] total_requests={total_requests}")
            
            if token_usage > 0:
                print("[OK] Dashboard shows non-zero token usage!")
            else:
                print("[ISSUE] Dashboard still shows 0 tokens!")
        else:
            print(f"[ERROR] Dashboard API response: {resp.text[:300]}")


async def decode_jwt_org(token: str) -> str:
    """Decode the JWT to get the org claim."""
    if token == "test":
        return "org-default"
    try:
        import jwt
        payload = jwt.decode(token, options={"verify_signature": False})
        return payload.get("org", "unknown")
    except Exception:
        return "unknown"


async def main():
    print("="*60)
    print("LIVE END-TO-END TELEMETRY AUDIT")
    print("="*60)
    
    # Step 1: Get token
    token = await get_token()
    org_id = await decode_jwt_org(token)
    print(f"[INFO] Using org_id: {org_id}")
    
    # Step 2: Make plan-with-ai request
    plan_result = await make_plan_request(token)
    
    # Small delay for async DB writes
    await asyncio.sleep(2)
    
    # Step 3: Check MongoDB
    await check_mongodb_docs(org_id)
    
    # Step 4: Check Dashboard API
    await check_dashboard_api(token)
    
    # Final summary
    print("\n" + "="*60)
    print("EVIDENCE SUMMARY")
    print("="*60)
    print(f"org_id used: {org_id}")
    print(f"plan-with-ai succeeded: {plan_result is not None}")


asyncio.run(main())
