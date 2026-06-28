from pathlib import Path
import sys

if __package__ in (None, ""):
    sys.path.append(str(Path(__file__).resolve().parent.parent))

try:
    from .models.task import ChatRequest
    from .database import db, get_db_status
    from .routes.tasks import router
    from .config import SLACK_TOKEN
except ImportError:
    from backend.models.task import ChatRequest
    from backend.database import db, get_db_status
    from backend.routes.tasks import router
    from backend.config import SLACK_TOKEN

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

print("Slack Token configured:", bool(SLACK_TOKEN))

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/")
def home():
    return {"message": "Sync Sphere Backend Running"}


@app.get("/test-db")
def test_db():
    collections = db.list_collection_names()
    return {"collections": collections}


@app.get("/db-status")
def db_status():
    return get_db_status()


@app.post("/chat")
def chat(request: ChatRequest):

    text = request.message.lower()

    if "task" in text:

        task = {
            "title": request.message,
            "assignedTo": "Dhruv",
            "status": "Pending"
        }

        db.tasks.insert_one(task)

        try:
            from backend.integrations.slack import notify_task_created
            notify_task_created(task["title"], task["assignedTo"], task["status"])
        except Exception as exc:
            print("Slack notification failed:", exc)

        return {
            "reply": "Task Created Successfully"
        }

    return {
        "reply": f"You said: {request.message}"
    }