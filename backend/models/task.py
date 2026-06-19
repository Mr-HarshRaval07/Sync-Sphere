from pydantic import BaseModel

class Task(BaseModel):
    title: str
    assignedTo: str
    status: str

class ChatRequest(BaseModel):
    message: str