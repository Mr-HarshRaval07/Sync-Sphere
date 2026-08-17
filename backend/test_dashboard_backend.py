import asyncio
import os
import sys

# Ensure src is in PYTHONPATH
sys.path.insert(0, os.path.abspath('./src'))

from syncsphere.infrastructure.di.container import Container
from syncsphere.iam.infrastructure.documents.organization_document import OrganizationDocument

async def main():
    container = Container()
    await container.init_resources()
    org = await OrganizationDocument.find_one()
    if not org:
        print("No organization found.")
        return
        
    dashboard = await container.observability_service.get_metrics_dashboard(str(org.id))
    print(dashboard.model_dump_json(indent=2))

if __name__ == "__main__":
    asyncio.run(main())
