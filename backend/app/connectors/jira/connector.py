from typing import Any

from app.connectors.base import BaseConnector
from app.connectors.jira.service import JiraService


class JiraConnector(BaseConnector):

    def __init__(self):
        self.service = JiraService()

    async def connect(self):
        # Stateless HTTP API
        return True

    async def disconnect(self):
        return True

    async def execute(
        self,
        action: str,
        payload: dict,
        context: dict[str, Any] | None = None,
    ) -> dict:

        if action == "create_issue":
            result = await self.service.create_issue(
                summary=payload["summary"],
                issue_type=payload.get("issue_type", "Task"),
                description=payload.get("description", "")
            )

            return result

        raise ValueError(f"Unsupported Jira action: {action}")