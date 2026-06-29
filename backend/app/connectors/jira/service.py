from app.connectors.jira.client import JiraClient
from app.core.config import settings


class JiraService:

    def __init__(self):
        self.client = JiraClient()

    async def create_issue(
        self,
        summary: str,
        issue_type: str = "Task",
        description: str = ""
    ):

        payload = {
            "fields": {
                "project": {
                    "key": settings.JIRA_PROJECT_KEY
                },
                "summary": summary,
                "issuetype": {
                    "name": issue_type
                }
            }
        }

        # Add description only if provided
        if description:
            payload["fields"]["description"] = {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [
                            {
                                "type": "text",
                                "text": description
                            }
                        ]
                    }
                ]
            }

        response = await self.client.create_issue(payload)

        if response.status_code != 201:
            raise Exception(
                f"Jira Error ({response.status_code}): {response.text}"
            )

        return response.json()