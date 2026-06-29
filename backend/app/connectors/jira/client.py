import httpx

from app.core.config import settings


class JiraClient:

    def __init__(self):
        self.base_url = settings.JIRA_BASE_URL
        self.auth = (
            settings.JIRA_EMAIL,
            settings.JIRA_API_TOKEN
        )

        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    async def create_issue(self, payload: dict):

        url = f"{self.base_url}/rest/api/3/issue"

        async with httpx.AsyncClient() as client:

            response = await client.post(
                url=url,
                auth=self.auth,
                headers=self.headers,
                json=payload,
            )

        return response