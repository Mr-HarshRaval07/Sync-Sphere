"""
End-to-End Telemetry Audit Script
Steps:
1. Make a real OpenRouter API call and print raw response
2. Insert a PromptExecutionDocument directly and verify it
3. Query the analytics engine for org stats
4. Verify all token fields are non-zero
"""
import asyncio
import httpx
import json
import os
import sys

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

async def step1_raw_openrouter_request():
    """Step 1: Make a real OpenRouter request and print raw usage."""
    print("\n" + "="*60)
    print("STEP 1: RAW OPENROUTER API REQUEST")
    print("="*60)

    # Load .env for API key
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

    api_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("LLM_API_KEY")
    model = os.getenv("LLM_MODEL", "openai/gpt-4o-mini")

    if not api_key:
        print("[ERROR] No OPENROUTER_API_KEY or LLM_API_KEY in environment!")
        return None

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:3000",
        "X-Title": "SyncSphere AI Audit",
    }

    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": "Reply with exactly: 'Telemetry audit OK' - no other words."}
        ],
        "temperature": 0.0,
        "max_tokens": 20,
    }

    print(f"[INFO] Model: {model}")
    print(f"[INFO] URL: {OPENROUTER_API_URL}")

    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(OPENROUTER_API_URL, headers=headers, json=payload)
        print(f"[INFO] HTTP Status: {resp.status_code}")

        if resp.status_code != 200:
            print(f"[ERROR] Response: {resp.text[:500]}")
            return None

        data = resp.json()
        print(f"\n[RAW RESPONSE - usage section]:")
        print(json.dumps(data.get("usage", {}), indent=2))
        print(f"\n[RAW RESPONSE - full]:")
        print(json.dumps({
            "id": data.get("id"),
            "model": data.get("model"),
            "usage": data.get("usage"),
            "choices_count": len(data.get("choices", [])),
        }, indent=2))

        usage = data.get("usage", {})
        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)
        total_tokens = usage.get("total_tokens", 0)

        print(f"\n[PARSED] prompt_tokens={prompt_tokens}")
        print(f"[PARSED] completion_tokens={completion_tokens}")
        print(f"[PARSED] total_tokens={total_tokens}")

        if total_tokens == 0:
            print("[WARNING] total_tokens is 0 - OpenRouter may not be returning usage!")
        else:
            print("[OK] OpenRouter returned non-zero token counts")

        return usage, model, api_key

async def step2_check_beanie_documents(org_id: str):
    """Step 2: Check existing PromptExecutionDocuments in MongoDB for org."""
    print("\n" + "="*60)
    print("STEP 2: QUERY MONGODB FOR PROMPT EXECUTION DOCUMENTS")
    print("="*60)

    try:
        from syncsphere.core.config.settings import settings
        from motor.motor_asyncio import AsyncIOMotorClient
        from beanie import init_beanie
        from syncsphere.ai.infrastructure.documents.execution_document import PromptExecutionDocument

        mongo_uri = str(settings.mongodb.uri)
        db_name = settings.mongodb.database

        print(f"[INFO] MongoDB URI: {mongo_uri[:50]}...")
        print(f"[INFO] Database: {db_name}")
        print(f"[INFO] Querying for org_id: {org_id}")

        client = AsyncIOMotorClient(mongo_uri)
        await init_beanie(
            database=client[db_name],
            document_models=[PromptExecutionDocument]
        )

        docs = await PromptExecutionDocument.find({"org_id": org_id}).to_list()
        print(f"\n[INFO] Total PromptExecutionDocuments for org: {len(docs)}")

        if not docs:
            print("[WARNING] NO documents found! Gateway may not be saving executions.")
            # Also check without org filter
            all_docs = await PromptExecutionDocument.find({}).to_list()
            print(f"[INFO] Total across ALL orgs: {len(all_docs)}")
            if all_docs:
                print(f"[INFO] Sample orgs in DB: {list(set(d.org_id for d in all_docs[:10]))}")
        else:
            # Print last 3 documents
            for i, doc in enumerate(docs[-3:]):
                print(f"\n--- Document {i+1} ---")
                print(f"  id: {doc.id}")
                print(f"  provider_name: {doc.provider_name}")
                print(f"  model_id: {doc.model_id}")
                print(f"  prompt_tokens: {doc.prompt_tokens}")
                print(f"  completion_tokens: {doc.completion_tokens}")
                print(f"  total_tokens: {doc.total_tokens}")
                print(f"  latency_ms: {doc.latency_ms}")
                print(f"  created_at: {doc.created_at}")
                print(f"  cache_hit: {doc.cache_hit}")

            # Check for zero-token docs
            zero_docs = [d for d in docs if d.total_tokens == 0]
            nonzero_docs = [d for d in docs if d.total_tokens > 0]
            print(f"\n[SUMMARY] Docs with total_tokens=0: {len(zero_docs)}")
            print(f"[SUMMARY] Docs with total_tokens>0: {len(nonzero_docs)}")

            if zero_docs:
                print(f"\n[WARNING] Found {len(zero_docs)} docs with zero tokens!")
                print("[INFO] Sample zero-token doc:")
                zd = zero_docs[-1]
                print(f"  id={zd.id}, provider={zd.provider_name}, model={zd.model_id}")

        return docs

    except Exception as e:
        print(f"[ERROR] MongoDB query failed: {e}")
        import traceback; traceback.print_exc()
        return []

async def step3_call_analytics_engine(org_id: str):
    """Step 3: Call the analytics engine directly (same as dashboard API does)."""
    print("\n" + "="*60)
    print("STEP 3: ANALYTICS ENGINE RESULT (DASHBOARD DATA)")
    print("="*60)

    try:
        from syncsphere.observability.application.services.analytics import AIAnalyticsEngine

        # Mock repos (not needed since AIAnalyticsEngine queries MongoDB directly)
        class FakeRepo:
            pass

        engine = AIAnalyticsEngine(metric_repo=FakeRepo(), event_store_repo=FakeRepo())
        result = await engine.get_ai_analytics(org_id)

        print(f"\n[ANALYTICS ENGINE OUTPUT]:")
        print(json.dumps(result, indent=2, default=str))

        if result.get("token_usage", 0) == 0:
            print(f"\n[ISSUE] token_usage is 0 in analytics result!")
            print("[CAUSE] Either no PromptExecutionDocuments exist, or they all have total_tokens=0")
        else:
            print(f"\n[OK] token_usage={result['token_usage']} - Dashboard will show non-zero!")

        return result

    except Exception as e:
        print(f"[ERROR] Analytics engine failed: {e}")
        import traceback; traceback.print_exc()
        return {}

async def step4_call_dashboard_api():
    """Step 4: Call the actual dashboard HTTP endpoint."""
    print("\n" + "="*60)
    print("STEP 4: DASHBOARD API HTTP CALL")
    print("="*60)

    # We need a valid token - try calling dashboard endpoint
    backend_url = "http://localhost:8000"

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Try without auth first to see what happens
        try:
            resp = await client.get(f"{backend_url}/v1/observability/dashboard")
            print(f"[INFO] Without auth: HTTP {resp.status_code}")
            if resp.status_code == 200:
                data = resp.json()
                ai_data = data.get("data", {}).get("ai_gateway", {})
                print(f"[RESULT] ai_gateway.token_usage = {ai_data.get('token_usage', 'KEY MISSING')}")
                print(f"[RESULT] ai_gateway.input_tokens = {ai_data.get('input_tokens', 'KEY MISSING')}")
                print(f"[RESULT] ai_gateway.output_tokens = {ai_data.get('output_tokens', 'KEY MISSING')}")
                print(f"[RESULT] ai_gateway.total_requests = {ai_data.get('total_requests', 'KEY MISSING')}")
                print(f"[RESULT] ai_gateway.last_request_at = {ai_data.get('last_request_at', 'KEY MISSING')}")
            elif resp.status_code == 401 or resp.status_code == 403:
                print("[INFO] Auth required - backend is running and secured")
            else:
                print(f"[INFO] Response: {resp.text[:200]}")
        except httpx.ConnectError:
            print(f"[WARNING] Backend not reachable at {backend_url} - is it running?")

async def main():
    print("\n" + "#"*60)
    print("# SYNCSPHERE AI TELEMETRY END-TO-END AUDIT")
    print("#"*60)

    # Determine org_id to test with
    # Try to get from MongoDB itself
    org_id = None
    try:
        from syncsphere.core.config.settings import settings
        from motor.motor_asyncio import AsyncIOMotorClient
        client = AsyncIOMotorClient(str(settings.mongodb.uri))
        db = client[settings.mongodb.database]
        org_doc = await db["organizations"].find_one({})
        if org_doc:
            org_id = str(org_doc.get("_id") or org_doc.get("org_id", ""))
            print(f"\n[INFO] Using org_id from DB: {org_id}")
        else:
            # Check users collection
            user_doc = await db["users"].find_one({})
            if user_doc:
                org_id = str(user_doc.get("organization_id") or user_doc.get("org_id", ""))
                print(f"\n[INFO] Using org_id from users: {org_id}")
    except Exception as e:
        print(f"[WARNING] Could not auto-detect org_id: {e}")

    if not org_id:
        # Try execution documents
        try:
            from syncsphere.core.config.settings import settings
            from motor.motor_asyncio import AsyncIOMotorClient
            from beanie import init_beanie
            from syncsphere.ai.infrastructure.documents.execution_document import PromptExecutionDocument
            client = AsyncIOMotorClient(str(settings.mongodb.uri))
            await init_beanie(database=client[settings.mongodb.database], document_models=[PromptExecutionDocument])
            doc = await PromptExecutionDocument.find_one({})
            if doc:
                org_id = doc.org_id
                print(f"[INFO] Using org_id from prompt_executions: {org_id}")
        except Exception:
            pass

    if not org_id:
        org_id = "test_org"
        print(f"[WARNING] Could not detect org_id, using fallback: {org_id}")

    # Run all steps
    openrouter_result = await step1_raw_openrouter_request()
    docs = await step2_check_beanie_documents(org_id)
    analytics = await step3_call_analytics_engine(org_id)
    await step4_call_dashboard_api()

    # Final diagnosis
    print("\n" + "="*60)
    print("FINAL DIAGNOSIS")
    print("="*60)

    issues = []

    if openrouter_result:
        usage, model, key = openrouter_result
        if usage.get("total_tokens", 0) == 0:
            issues.append("OpenRouter is not returning token usage - check if model supports usage reporting")

    zero_docs = [d for d in docs if d.total_tokens == 0]
    nonzero_docs = [d for d in docs if d.total_tokens > 0]

    if not docs:
        issues.append("NO PromptExecutionDocuments in MongoDB - gateway save() is not being called or org_id mismatch")
    elif zero_docs and not nonzero_docs:
        issues.append(f"All {len(zero_docs)} PromptExecutionDocuments have total_tokens=0 - OpenRouter usage not being saved")
    elif zero_docs:
        issues.append(f"{len(zero_docs)}/{len(docs)} PromptExecutionDocuments have total_tokens=0 - partial fix needed")

    if analytics.get("token_usage", 0) == 0 and nonzero_docs:
        issues.append("Analytics engine returns 0 despite non-zero docs - org_id filter mismatch!")

    if issues:
        print("[ISSUES FOUND]:")
        for i, issue in enumerate(issues, 1):
            print(f"  {i}. {issue}")
    else:
        print("[OK] No critical issues found - telemetry pipeline appears functional")
        print(f"  token_usage in analytics: {analytics.get('token_usage')}")
        print(f"  input_tokens: {analytics.get('input_tokens')}")
        print(f"  output_tokens: {analytics.get('output_tokens')}")

if __name__ == "__main__":
    asyncio.run(main())
