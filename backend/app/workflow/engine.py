from app.schemas.workflow import WorkflowPlan
from app.workflow.registry import ConnectorRegistry


class WorkflowEngine:

    def __init__(self, registry: ConnectorRegistry):
        self.registry = registry

    async def execute(self, plan: WorkflowPlan):

        for step in plan.steps:

            connector = self.registry.get(step.service.value)

            await connector.connect()

            result = await connector.execute(
                action=step.action,
                payload=step.parameters,
            )

            await connector.disconnect()

            print(result)