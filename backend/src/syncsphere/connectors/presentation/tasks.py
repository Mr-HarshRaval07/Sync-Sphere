from fastapi import APIRouter
from pydantic import BaseModel
import httpx
import os

router = APIRouter(prefix="/tasks", tags=["Tasks"])


class TaskCreate(BaseModel):
    title: str
    assigned_to: str
    status: str


SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")

CHANNEL_ID = os.getenv("SLACK_CHANNEL_ID")


@router.post("/")
async def create_task(task: TaskCreate):

    message = f"""
📌 New Task Created

Title: {task.title}

Assigned To: {task.assigned_to}

Status: {task.status}
"""

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://slack.com/api/chat.postMessage",
        headers={
            "Authorization": f"Bearer {SLACK_BOT_TOKEN}",
            "Content-Type": "application/json",
        },
        json={
            "channel": CHANNEL_ID,
            "text": message,
        },
    )
    result = response.json()


    print("\n========== SLACK RESPONSE ==========")
    print(result)
    print("====================================\n")
