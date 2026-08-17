import asyncio
import sys
import logging
from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

# Setup minimal path to import SyncSphere
sys.path.append("d:/syncsphere 01/syncsphere 01/backend/src")

from syncsphere.core.config.settings import settings
from syncsphere.approval.infrastructure.documents.approval_request_document import ApprovalRequestDocument
from syncsphere.approval.infrastructure.mappers import ApprovalMapper
from syncsphere.tasks.documents import WorkflowExecutionLogDocument, AutomationWorkflowDocument
from syncsphere.core.dependency_injection.container import container

async def main():
    logging.basicConfig(level=logging.INFO)
    print("Connecting to MongoDB...")
    client = AsyncIOMotorClient(settings.database.uri)
    db = client[settings.database.database]
    
    await init_beanie(
        database=db,
        document_models=[
            ApprovalRequestDocument,
            WorkflowExecutionLogDocument,
            AutomationWorkflowDocument
        ]
    )
    
    docs = await ApprovalRequestDocument.find_all().sort("-created_at").limit(1).to_list()
    if not docs:
        print("no docs")
        return
        
    doc = docs[0]
    print(f"Trying to approve doc: {doc.id}")
    try:
        approval = await container.approval_request_repo.get_by_id(str(doc.id))
        stage = approval.chain.stages[approval.chain.current_stage_index]
        assignee_id = stage.assignments[0].user_id if stage.assignments and stage.assignments[0].user_id else "test_user"
        print(f"Approving as user: {assignee_id}")
        
        from syncsphere.approval.application.commands import ApproveCommand
        cmd = ApproveCommand(
            org_id=approval.org_id,
            approval_id=str(approval.id),
            user_id=assignee_id,
            comment="Test auto approve"
        )
        res = await container.approval_service.submit_approval(cmd)
        print(f"Service res: {res.is_ok}, fail: {res.error() if res.is_fail else 'None'}")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    asyncio.run(main())
