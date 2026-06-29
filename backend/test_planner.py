import asyncio

from app.planner.planner import Planner


async def main():

    planner = Planner()

    plan = await planner.create_plan(
        "Create a Jira bug called Login Error and notify Slack."
    )

    print(plan.model_dump_json(indent=4))


asyncio.run(main())