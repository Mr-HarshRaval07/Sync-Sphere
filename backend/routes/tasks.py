from pathlib import Path
import sys
from threading import Thread

if __package__ in (None, ""):
    sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from fastapi import APIRouter

try:
    from ..database import db
    from ..models.task import Task
    from ..integrations.slack import notify_task_created
    from ..integrations.github import create_github_issue

except ImportError:
    from backend.database import db
    from backend.models.task import Task
    from backend.integrations.slack import notify_task_created
    from backend.integrations.github import create_github_issue


router = APIRouter()


# Create Task
@router.post("/tasks")
def create_task(task: Task):

    print("Received task:", task)

    # Store in MongoDB (NO AI SUMMARY NOW)
    result = db.tasks.insert_one({
        "title": task.title,
        "assignedTo": task.assignedTo,
        "status": task.status
    })

    print("Inserted ID:", result.inserted_id)

    # Slack notification
    Thread(
        target=notify_task_created,
        args=(task.title, task.assignedTo, task.status),
        daemon=True
    ).start()

    # GitHub Issue
    Thread(
        target=create_github_issue,
        args=(task.title, task.assignedTo, task.status),
        daemon=True
    ).start()

    return {
        "message": "Task Created"
    }


# Read Tasks
@router.get("/tasks")
def get_tasks():

    tasks = list(
        db.tasks.find(
            {},
            {"_id": 0}
        )
    )

    return tasks


# Update Task
@router.put("/tasks/{title}")
def update_task(title: str):

    db.tasks.update_one(
        {"title": title},
        {
            "$set": {
                "status": "Completed"
            }
        }
    )

    return {
        "message": "Task Updated"
    }


# Delete Task
@router.delete("/tasks/{title}")
def delete_task(title: str):

    db.tasks.delete_one(
        {"title": title}
    )

    return {
        "message": "Task Deleted"
    }