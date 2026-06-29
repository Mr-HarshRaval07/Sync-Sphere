from enum import Enum
from typing import Any

from pydantic import BaseModel


class Service(str, Enum):
    JIRA = "jira"
    SLACK = "slack"
    GITHUB = "github"
    GOOGLE_SHEETS = "google_sheets"


class WorkflowStep(BaseModel):
    step: int
    service: Service
    action: str
    parameters: dict[str, Any]


class WorkflowPlan(BaseModel):
    steps: list[WorkflowStep]