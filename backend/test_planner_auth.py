import asyncio
from syncsphere.core.dependency_injection.container import container
from syncsphere.tasks.schemas import CreateTaskRequest
from syncsphere.core.config.settings import settings

async def main():
    await container.mongo_motor_db.command("ping")
    from syncsphere.tasks.router import create_task
    from fastapi import Request
    
    class DummyRequest:
        state = type("State", (), {"correlation_id": "test_id"})()
        
    req = DummyRequest()
    from syncsphere.identity.infrastructure.documents import UserDocument, OrgDocument
    org = await OrgDocument.find_one({})
    
    # Let's hit plan_with_ai first to see what it generates!
    from syncsphere.tasks.router import plan_with_ai
    from syncsphere.tasks.schemas import PlanTaskRequest
    
    plan_req = PlanTaskRequest(prompt="Send an email to unauthorized_person@gmail.com")
    res = await plan_with_ai(req, plan_req, claims={"org": str(org.id)})
    print("PLAN OUPUT (NONE SENDER):")
    import json; print(json.dumps(res, indent=2))
    
    plan_req2 = PlanTaskRequest(prompt="Send an email from unconnected_friend@gmail.com to abc@gmail.com")
    res2 = await plan_with_ai(req, plan_req2, claims={"org": str(org.id)})
    print("PLAN OUTPUT (EXPLICIT SENDER):")
    print(json.dumps(res2, indent=2))

if __name__ == "__main__":
    asyncio.run(main())
