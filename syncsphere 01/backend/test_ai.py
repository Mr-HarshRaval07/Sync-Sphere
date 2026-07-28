import asyncio
import httpx

async def submit_prompt():
    prompt = "Launch my new website next Friday. Create a GitHub issue for the development team, notify the team on Slack, send an email to the client at client@example.com, schedule a launch meeting on Google Calendar, and add the project summary to Google Sheets."
    headers = {"Cookie": "session=..."} # without real auth I might get 401. I'll mock the internal call instead! 
import sys
from dotenv import load_dotenv
from syncsphere.tasks.router import plan_with_ai
from syncsphere.tasks.schemas import PlanWithAIRequest
from fastapi import Request
from dataclasses import dataclass

@dataclass
class State:
    correlation_id: str = "123"

class MockRequest:
    state = State()

async def main():
    load_dotenv()
    prompt_text = "Create a high priority task called Launch SyncSphere Website, assign it to Janhvi, and complete it by August 15 2026. Create a GitHub issue, notify Slack, send an email, create a Calendar deadline event, and add the task to Google Sheets."
    req = PlanWithAIRequest(prompt=prompt_text)
    
    # We must init beanie to use the Models dynamically inside plan_with_ai
    from motor.motor_asyncio import AsyncIOMotorClient
    from beanie import init_beanie
    import os
    mc = AsyncIOMotorClient(os.getenv("SYNCSPHERE_MONGODB_URI", "mongodb://localhost:27017"))
    from syncsphere.tasks.documents import TaskDocument, WorkflowExecutionLogDocument, GoogleTokenDocument, SlackTokenDocument, AutomationWorkflowDocument, GitHubTokenDocument
    await init_beanie(database=mc["syncsphere"], document_models=[TaskDocument, WorkflowExecutionLogDocument, GoogleTokenDocument, SlackTokenDocument, AutomationWorkflowDocument, GitHubTokenDocument])

    # Let's hit the container
    try:
        res = await plan_with_ai(request=MockRequest(), body=req, claims={"org": "testorg"})
        print("AI Planner output:")
        import json
        print(json.dumps(res, indent=2))
        
        # Test Confirm Plan
        from syncsphere.tasks.schemas import ConfirmPlanRequest, CreateTaskRequest
        from syncsphere.tasks.router import confirm_plan
        from fastapi import BackgroundTasks
        
        task_data = res["data"]["task"]
        integrations = res["data"]["integrations"]
        from pydantic import BaseModel
        class Autom(BaseModel):
            action: str
            config: dict
        
        auto_objs = [Autom(action=i["action"], config=i["config"]) for i in integrations if i["selected"]]
        create_task = CreateTaskRequest(
            title=task_data["title"],
            description=task_data["description"],
            assigned_to=task_data.get("assignee"),
            priority=task_data["priority"],
            status=task_data["status"],
            due_date=task_data.get("due_date"),
            automations=auto_objs
        )
        confirm_req = ConfirmPlanRequest(tasks=[create_task])
        bg = BackgroundTasks()
        print("\n\n--- Executing Confirm Plan ---")
        confirm_res = await confirm_plan(request=MockRequest(), body=confirm_req, background_tasks=bg, claims={"org": "testorg"})
        print("Confirm Plan output:")
        print(json.dumps(confirm_res, indent=2))
        
        # Run background tasks manually
        print("\n\n--- Running Background Integrations ---")
        for task in bg.tasks:
            await task.func(*task.args, **task.kwargs)
            
    except Exception as e:
        import traceback
        traceback.print_exc()

asyncio.run(main())
