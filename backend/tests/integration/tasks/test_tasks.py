import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from syncsphere.main import app

client = TestClient(app)


def test_tasks_crud_lifecycle_flow(mock_task_coll, mock_slack_coll):
    # 1. Register and Login to get jwt header
    register_payload = {
        "email": "taskadmin2@acme.ai",
        "password": "supersecretpassword123!",
        "first_name": "Task",
        "last_name": "Master",
        "org_name": "Task Corp",
        "org_slug": "task-corp-2"
    }
    client.post("/v1/auth/register", json=register_payload)
    
    resp_login = client.post("/v1/auth/login", json={
        "email": "taskadmin2@acme.ai",
        "password": "supersecretpassword123!"
    })
    access_token = resp_login.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    # Setup mock tasks and slack tokens instances
    mock_token = MagicMock()
    mock_token.access_token = "xoxb-mock-access-token"
    mock_token.team_name = "Slack Team"
    mock_token.team_id = "T123"

    mock_task = MagicMock()
    mock_task.id = "60c72b2f9b1d8e2b8c8b4567"
    mock_task.org_id = "test-org-id"
    mock_task.title = "Build UI Mockups"
    mock_task.description = "Construct the high fidelity React screens"
    mock_task.assigned_to = "Alice Jones"
    mock_task.priority = "High"
    mock_task.status = "Pending"
    mock_task.due_date = "2026-08-01"
    mock_task.created_at = None
    mock_task.updated_at = None

    # We will patch the Beanie queries for TaskDocument and SlackTokenDocument
    with patch("syncsphere.tasks.documents.SlackTokenDocument.find_one", new_callable=AsyncMock) as mock_slack_find_one, \
     patch("syncsphere.tasks.documents.TaskDocument.insert", new_callable=AsyncMock) as mock_task_insert, \
     patch("syncsphere.tasks.documents.TaskDocument.find", new_callable=MagicMock) as mock_task_find, \
     patch("syncsphere.tasks.documents.TaskDocument.find_one", new_callable=AsyncMock) as mock_task_find_one, \
     patch("syncsphere.tasks.documents.TaskDocument.save", new_callable=AsyncMock) as mock_task_save, \
     patch("syncsphere.tasks.documents.TaskDocument.delete", new_callable=AsyncMock) as mock_task_delete, \
     patch("syncsphere.tasks.router._post_slack_message_legacy", new_callable=AsyncMock) as mock_slack_notifier, \
     patch("syncsphere.tasks.documents.TaskDocument.get_motor_collection", create=True), \
     patch("syncsphere.tasks.documents.SlackTokenDocument.get_motor_collection", create=True):
         
        mock_slack_find_one.return_value = mock_token
        mock_task_insert.return_value = mock_task
        mock_task_save.return_value = mock_task
        mock_task_delete.return_value = None

        # Mock TaskDocument.find(...) search result chain
        mock_query = MagicMock()
        mock_query.sort.return_value = mock_query
        mock_query.to_list = AsyncMock(return_value=[mock_task])
        mock_task_find.return_value = mock_query

        # Mock TaskDocument.find_one(...)
        mock_task_find_one.return_value = mock_task

        # Test POST /v1/tasks
        task_payload = {
            "title": "Build UI Mockups",
            "description": "Construct the high fidelity React screens",
            "assigned_to": "Alice Jones",
            "priority": "High",
            "status": "Pending",
            "due_date": "2026-08-01"
        }
        resp_create = client.post("/v1/tasks", json=task_payload, headers=headers)
        assert resp_create.status_code == 201

        # Verify Slack notifier was called
        mock_slack_notifier.assert_called_once()
        called_task = mock_slack_notifier.call_args[0][0]
        assert called_task.title == "Build UI Mockups"

        # Test GET /v1/tasks
        resp_list = client.get("/v1/tasks", headers=headers)
        assert resp_list.status_code == 200
        tasks = resp_list.json()["data"]
        assert len(tasks) == 1
        assert tasks[0]["title"] == "Build UI Mockups"

        # Test GET /v1/tasks/{id}
        resp_get = client.get("/v1/tasks/60c72b2f9b1d8e2b8c8b4567", headers=headers)
        assert resp_get.status_code == 200
        assert resp_get.json()["data"]["title"] == "Build UI Mockups"

        # Test PUT /v1/tasks/{id}
        update_payload = {
            "status": "In Progress"
        }
        resp_update = client.put("/v1/tasks/60c72b2f9b1d8e2b8c8b4567", json=update_payload, headers=headers)
        assert resp_update.status_code == 200
        
        # Test DELETE /v1/tasks/{id}
        resp_delete = client.delete("/v1/tasks/60c72b2f9b1d8e2b8c8b4567", headers=headers)
        assert resp_delete.status_code == 200
