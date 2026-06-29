from pydantic import BaseModel


class ProcessRequest(BaseModel):
    prompt: str


class ProcessResponse(BaseModel):
    status: str
    message: str
    workflow: dict | None = None