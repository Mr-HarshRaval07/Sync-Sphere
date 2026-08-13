import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from pydantic import Field
from typing import Optional, List, Dict, Any
from syncsphere.approval.infrastructure.documents.approval_request_document import ApprovalRequestDocument
from syncsphere.shared_kernel.infrastructure.mongodb.base_document import BaseTenantDocument
import sys

async def main():
    try:
        client = AsyncIOMotorClient('mongodb+srv://syncsphere:SyncSphere123@cluster0.zoo2vpl.mongodb.net/?appName=Cluster0')
        db = client['syncsphere']
        await init_beanie(database=db, document_models=[ApprovalRequestDocument])
        
        target = "eff7abda-4100-4bd9-8ac8-73cfce321af6" # from previous output
        
        doc = await ApprovalRequestDocument.get(target)
        print(f"Target Org: {doc.org_id} (Type: {type(doc.org_id)})")
        
    except Exception as e:
        print(e)
        import traceback
        traceback.print_exc()

asyncio.run(main())
