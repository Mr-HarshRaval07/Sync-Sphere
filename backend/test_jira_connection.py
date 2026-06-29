import asyncio

from app.connectors.jira.client import JiraClient
from app.core.config import settings


async def main():
    client = JiraClient()

    payload = {
        "fields": {
            "project": {
                "key": settings.JIRA_PROJECT_KEY
            },
            "summary": "Sync Sphere Test Issue",
            "description": {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [
                            {
                                "type": "text",
                                "text": "This issue was created from Sync Sphere 🚀"
                            }
                        ]
                    }
                ]
            },
            "issuetype": {
                "name": "Task"
            }
        }
    }

    response = await client.create_issue(payload)

    print("Status Code:", response.status_code)
    print("Response:")
    print(response.text)


if __name__ == "__main__":
    asyncio.run(main())