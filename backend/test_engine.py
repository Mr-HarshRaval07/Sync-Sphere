import asyncio

from app.connectors.mock import MockConnector
from app.planner.planner import Planner
from app.workflow.engine import WorkflowEngine
from app.workflow.registry import ConnectorRegistry


async def main():
    planner = Planner()

    plan = await planner.create_plan(
        "Create a Jira bug named Login Error and notify Slack."
    )

    registry = ConnectorRegistry()

    # Register mock for now
    registry.register("jira", MockConnector())
    registry.register("slack", MockConnector())

    engine = WorkflowEngine(registry)

    await engine.execute(plan)


asyncio.run(main())