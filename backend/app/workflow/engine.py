from app.schemas.workflow import WorkflowPlan
from app.workflow.registry import ConnectorRegistry


class WorkflowEngine:
    def __init__(self, registry: ConnectorRegistry):
        self.registry = registry

    async def execute(self, plan: WorkflowPlan):
        """
        Executes each workflow step sequentially.

        Returns:
            {
                "status": "success",
                "results": {
                    "jira": {...},
                    "slack": {...}
                }
            }
        """

        context: dict[str, dict] = {}

        for step in plan.steps:

            connector = self.registry.get(step.service.value)

            await connector.connect()

            try:
                # Pass previous step results to the connector.
                result = await connector.execute(
                    action=step.action,
                    payload=step.parameters,
                    context=context,
                )

            finally:
                await connector.disconnect()

            # Store this connector's output for future workflow steps.
            context[step.service.value] = result

        return {
            "status": "success",
            "results": context,
        }