from models.task import ChatRequest
from fastapi import FastAPI
from database import db
from routes.tasks import router 
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
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
    collections=db.list_collection_names()
    return {"collections": collections}

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

        return {
            "reply": "Task Created Successfully"
        }

    return {
        "reply": f"You said: {request.message}"
    }