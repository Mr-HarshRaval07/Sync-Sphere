from pydantic import BaseModel, Field
from typing import Optional, Literal, List
from datetime import datetime


class TaskAutomationSchema(BaseModel):
    action: str
    config: dict = Field(default_factory=dict)
    status: str = "pending"
    error: Optional[str] = None
    executed_at: Optional[datetime] = None
    result: Optional[dict] = None


class CreateTaskRequest(BaseModel):
    title: str = Field(..., min_length=1, description="Task title")
    description: str = Field(default="", description="Task description")
    assigned_to: str = Field(default="", description="Assignee name or user id")
    priority: Literal["High", "Medium", "Low"] = Field(default="Medium")
    status: Literal["Pending", "In Progress", "Completed"] = Field(default="Pending")
    due_date: Optional[str] = Field(default=None, description="Due date string, e.g. 2026-08-15")
    automations: List[TaskAutomationSchema] = Field(default_factory=list)


class UpdateTaskRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    assigned_to: Optional[str] = None
    priority: Optional[Literal["High", "Medium", "Low"]] = None
    status: Optional[Literal["Pending", "In Progress", "Completed"]] = None
    due_date: Optional[str] = None
    automations: Optional[List[TaskAutomationSchema]] = None


class TaskResponse(BaseModel):
    id: str
    org_id: str
    title: str
    description: str
    assigned_to: str
    priority: str
    status: str
    due_date: Optional[str]
    automations: List[TaskAutomationSchema] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class PlanWithAIRequest(BaseModel):
    prompt: str = Field(..., description="High-level project goal or task prompt")


class ConfirmPlanRequest(BaseModel):
    tasks: List[CreateTaskRequest] = Field(...)

