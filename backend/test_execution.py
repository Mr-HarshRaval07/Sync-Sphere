import asyncio, sys, json
from syncsphere.core.lifecycle.documents import init_db
from syncsphere.tasks.router import create_task
from syncsphere.tasks.schemas import CreateTaskRequest
from syncsphere.identity.infrastructure.documents import OrgDocument
from fastapi import Request, BackgroundTasks

class DummyRequest:
    state = type('S',(),{'correlation_id':'test1'})()

async def main():
    await init_db()
    org = await OrgDocument.find_one({})
    if not org:
        print("No org found.")
        sys.exit(1)
        
    req = CreateTaskRequest(
        title="Test Task",
        description="test",
        priority="high",
        status="active",
        due_date=None,
        automations=[
            {
                "action": "gmail.send_email",
                "config": {
                    "to": "some_random_person@gmail.com",
                    "subject": "Hello",
                    "body": "from syncsphere task",
                    "google_email": "some_random_person@gmail.com" # What if AI put the recipient here?
                }
            }
        ]
    )
    
    # 1. Test when the AI hallucinates the recipient into the sender field
    bg = BackgroundTasks()
    res1 = await create_task(DummyRequest(), req, bg, claims={"org": str(org.id)})
    
    # Run the background tasks explicitly since FastAPI usually does it
    for t in bg.tasks:
        await t.func(*t.args, **t.kwargs)
        
    # Let's wait a bit for async tasks launched via asyncio.create_task inside create_task
    await asyncio.sleep(2)
    
    from syncsphere.tasks.documents import TaskDocument
    doc1 = await TaskDocument.get(res1["data"].id)
    print("TASK 1 (EXPLICIT SENDER = RECIPIENT):")
    print(json.dumps([a.model_dump() for a in doc1.automations], default=str, indent=2))
    
    # 2. Test when AI behaves correctly (leaves sender empty)
    req.automations[0].config.pop("google_email")
    res2 = await create_task(DummyRequest(), req, bg, claims={"org": str(org.id)})
    await asyncio.sleep(2)
    doc2 = await TaskDocument.get(res2["data"].id)
    print("TASK 2 (NO EXPLICIT SENDER):")
    print(json.dumps([a.model_dump() for a in doc2.automations], default=str, indent=2))

if __name__ == "__main__":
    asyncio.run(main())
