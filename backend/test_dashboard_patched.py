import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath('src'))
sys.path.insert(0, os.path.abspath('.'))

import src.syncsphere.infrastructure.di.container
from src.syncsphere.infrastructure.di.container import Container
from src.syncsphere.iam.infrastructure.documents.organization_document import OrganizationDocument
import json

async def main():
    container = Container()
    await container.init_resources()
    org_id = "test_org"
        
    dashboard = await container.observability_service.dashboard_pipeline.compile_dashboard(org_id)
    print(json.dumps(dashboard, indent=2, default=str))

if __name__ == "__main__":
    asyncio.run(main())
