import pytest
import asyncio
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from syncsphere.main import app
from beanie import init_beanie
import motor.motor_asyncio
from syncsphere.tasks.documents import TaskDocument, TaskAutomation

client = TestClient(app)

@pytest.fixture(autouse=True)
async def init_beanie_test():
    cli = motor.motor_asyncio.AsyncIOMotorClient()
    db = cli["test_db"]
    await init_beanie(database=db, document_models=[TaskDocument])

@patch("syncsphere.tasks.documents.TaskDocument.get_motor_collection", create=True)
def test_tasks_ai_planning_flow(mock_task_coll):
    # Register/Login
    register_payload = {
        "email": "aiadmin@acme.ai",
        "password": "supersecretpassword123!",
        "first_name": "AI",
        "last_name": "User",
        "org_name": "AI Corp",
        "org_slug": "ai-corp"
    }
    client.post("/v1/auth/register", json=register_payload)
    
    resp_login = client.post("/v1/auth/login", json={
        "email": "aiadmin@acme.ai",
        "password": "supersecretpassword123!"
    })
    access_token = resp_login.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    # Test /plan-with-ai endpoint
    from syncsphere.ai.domain.value_objects import StructuredOutputResult
    from syncsphere.core.dependency_injection.container import container

    mock_parsed_str = (
        '{"tasks": ['
        '  {"title": "Draft Gmail", "description": "Draft client email", "assigned_to": "Alice", "priority": "High",'
        '   "automation_action": "gmail.send_email", "automation_config": {"to": "bob@gmail.com", "subject": "Hi", "body": "Hello"}},'
        '  {"title": "Verify feedback", "description": "Manual verify", "assigned_to": "Bob", "priority": "Medium"}'
        ']}'
    )

    async def mock_structured_output(*args, **kwargs):
        return StructuredOutputResult(
            success=True,
            raw_output=mock_parsed_str
        )

    # Patch structured output
    container.ai_gateway.structured_output = mock_structured_output

    plan_payload = {"prompt": "Write email to Bob and manually review output"}
    resp_plan = client.post("/v1/tasks/plan-with-ai", json=plan_payload, headers=headers)
    assert resp_plan.status_code == 200
    planned_tasks = resp_plan.json()["data"]
    assert len(planned_tasks) == 2
    assert planned_tasks[0]["title"] == "Draft Gmail"
    assert planned_tasks[0]["automation_action"] == "gmail.send_email"

    # Test /confirm-plan endpoint
    mock_task = TaskDocument(
        id="60c72b2f9b1d8e2b8c8b4000",
        org_id="test-org",
        title="Draft Gmail",
        description="Draft client email",
        assigned_to="Alice",
        priority="High",
        status="Pending",
        due_date="2026-08-01",
        automation=TaskAutomation(
            action="gmail.send_email",
            config={"to": "bob@gmail.com", "subject": "Hi", "body": "Hello"},
            status="pending"
        )
    )

    confirm_payload = {
        "tasks": [
            {
                "title": "Draft Gmail",
                "description": "Draft client email",
                "assigned_to": "Alice",
                "priority": "High",
                "status": "Pending",
                "automation": {
                    "action": "gmail.send_email",
                    "config": {"to": "bob@gmail.com", "subject": "Hi", "body": "Hello"}
                }
            }
        ]
    }

    with patch("syncsphere.tasks.documents.TaskDocument.insert", new_callable=AsyncMock) as mock_insert, \
         patch("syncsphere.tasks.documents.TaskDocument.find_one", new_callable=AsyncMock) as mock_find_one, \
         patch("syncsphere.tasks.documents.TaskDocument.save", new_callable=AsyncMock) as mock_save, \
         patch("syncsphere.workflow.application.action_registry.ACTION_REGISTRY") as mock_action_registry:
         
         mock_insert.return_value = mock_task
         mock_find_one.return_value = mock_task
         mock_save.return_value = mock_task

         mock_gmail_fn = AsyncMock(return_value={"status": "sent"})
         mock_action_registry.get.return_value = mock_gmail_fn
         
         with patch("syncsphere.workflow.application.action_registry.get_action", return_value=mock_gmail_fn):
             resp_confirm = client.post("/v1/tasks/confirm-plan", json=confirm_payload, headers=headers)
             assert resp_confirm.status_code == 201
             assert mock_gmail_fn.call_count == 1

             resp_exec = client.post("/v1/tasks/60c72b2f9b1d8e2b8c8b4000/execute-automation", headers=headers)
             assert resp_exec.status_code == 200
             assert mock_gmail_fn.call_count == 2
             mock_gmail_fn.assert_called_with(to="bob@gmail.com", subject="Hi", body="Hello", org_id=mock_task.org_id)
