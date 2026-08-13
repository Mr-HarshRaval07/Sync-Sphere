import asyncio
import uuid
from motor.motor_asyncio import AsyncIOMotorClient
from syncsphere.core.config.settings import settings
from syncsphere.observability.application.services.analytics import RuntimeAnalytics
from beanie import init_beanie
from syncsphere.ai.infrastructure.documents.execution_document import PromptExecutionDocument
from syncsphere.tasks.documents import WorkflowExecutionLogDocument
from syncsphere.observability.infrastructure.documents.trace_document import TraceDocument
from syncsphere.workflow.infrastructure.documents.workflow_document import WorkflowDocument

# We need to initialize beanie to run the queries.
async def main():
    client = AsyncIOMotorClient(settings.mongodb_uri)
    db = client.get_database(settings.mongodb_database)
    await init_beanie(database=db, document_models=[PromptExecutionDocument, WorkflowExecutionLogDocument, TraceDocument, WorkflowDocument])

    # Try to find org_id
    latest_log = await WorkflowExecutionLogDocument.find_one()
    if not latest_log:
        print("No logs in DB.")
        return
    org_id = latest_log.organization_id
    print(f"Using org_id: {org_id}")

    analytics = RuntimeAnalytics(None)
    stats = await analytics.get_runtime_stats(org_id)
    import json
    with open('analytics_out.json', 'w') as f:
        json.dump(stats, f)
    print("Done")

if __name__ == "__main__":
    asyncio.run(main())
