import asyncio
import os
import sys
import traceback

sys.path.append(os.path.abspath('src'))

def log(msg):
    print(msg)
    with open("diag_plan.txt", "a", encoding="utf-8") as f:
        f.write(msg + "\n")

async def main():
    # Clear file
    open("diag_plan.txt", "w", encoding="utf-8").close()
    try:
        from syncsphere.main import app
        from syncsphere.tasks.router import plan_with_ai
        from syncsphere.tasks.schemas import PlanWithAIRequest
        
        async with app.router.lifespan_context(app):
            class MockRequest:
                def __init__(self):
                    self.state = type('State', (), {'correlation_id': 'diag-test'})()

            req = MockRequest()
            body = PlanWithAIRequest(prompt="Send an email with subject SyncSphere test and body Testing AI planning to my authorized Gmail account.")
            
            # Find an org_id
            from syncsphere.ai.infrastructure.documents import ModelProviderDocument
            providers = await ModelProviderDocument.find_all().to_list()
            org_id = providers[0].org_id if providers else "test-org"
            claims = {"org": org_id, "sub": "test-user"}
            
            log(f"Calling plan_with_ai with org_id: {org_id}")
            
            res = await plan_with_ai(request=req, body=body, claims=claims)
            log("PASS")
            import json
            log(json.dumps(res, default=str, indent=2))
        
    except Exception as e:
        log("FAIL (Exception)")
        log(f"Exception Type: {type(e).__name__}")
        log(f"Exception Message: {str(e)}")
        if hasattr(e, 'detail'):
            log(f"Exception Detail: {e.detail}")
        log("Traceback:")
        log(traceback.format_exc())

    # Ensure python flushes and exits cleanly to avoid hung processes
    os._exit(0)

if __name__ == "__main__":
    asyncio.run(main())
