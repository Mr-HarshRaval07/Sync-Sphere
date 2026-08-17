import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath('.'))

from syncsphere.infrastructure.mongodb.database import init_db
from syncsphere.iam.infrastructure.documents.organization_document import OrganizationDocument
from syncsphere.ai.infrastructure.documents.execution_document import PromptExecutionDocument
from syncsphere.tasks.documents import WorkflowExecutionLogDocument
from syncsphere.core.config.settings import settings
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie

async def main():
    # Basic Beanie init
    client = AsyncIOMotorClient(settings.database.mongodb_uri)
    db = client[settings.database.mongodb_db_name]
    await init_beanie(database=db, document_models=[
        OrganizationDocument,
        PromptExecutionDocument,
        WorkflowExecutionLogDocument
    ])

    org = await OrganizationDocument.find_one()
    if not org:
        print("No organization found.")
        return
        
    print(f"Org ID: {org.id}")
    
    ai_count = await PromptExecutionDocument.find({"org_id": str(org.id)}).count()
    print(f"Total AI Executions (org_id): {ai_count}")
    
    if ai_count > 0:
        latest = await PromptExecutionDocument.find({"org_id": str(org.id)}).sort("-created_at").limit(1).to_list()
        print(f"Latest AI Execution Date: {latest[0].created_at}")

    workflow_count = await WorkflowExecutionLogDocument.find({"organization_id": str(org.id)}).count()
    print(f"Total Workflow Executions: {workflow_count}")
    
    if workflow_count > 0:
        latest_wf = await WorkflowExecutionLogDocument.find({"organization_id": str(org.id)}).sort("-started_at").limit(1).to_list()
        print(f"Latest Workflow Execution Date: {latest_wf[0].started_at}")

if __name__ == "__main__":
    asyncio.run(main())
