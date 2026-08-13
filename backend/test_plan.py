import asyncio, json
import inspect
from syncsphere.core.dependency_injection.container import container
from syncsphere.tasks.schemas import PlanTaskRequest
from syncsphere.identity.infrastructure.documents import OrgDocument
from fastapi import Request

class DummyRequest:
    state = type('S',(),{'correlation_id':'t'})()

async def main():
    await container.init_repos()
    org = await OrgDocument.find_one({})
    from syncsphere.tasks.router import plan_with_ai
    
    req = PlanTaskRequest(prompt="Send an email from unconnected_friend@gmail.com to abc@gmail.com")
    res = await plan_with_ai(DummyRequest(), req, claims={"org": str(org.id)})
    print(json.dumps(res, indent=2))

if __name__ == "__main__":
    asyncio.run(main())
