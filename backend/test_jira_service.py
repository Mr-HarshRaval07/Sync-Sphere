import asyncio

from app.connectors.jira.service import JiraService


async def main():

    service = JiraService()

    result = await service.create_issue(
        summary="Created from Jira Service",
        description="This issue was created via the JiraService layer."
    )

    print(result)


asyncio.run(main())