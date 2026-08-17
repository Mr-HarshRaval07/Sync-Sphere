
import asyncio, sys, json
sys.path.insert(0, 'src')

async def run_test():
    # Setup Beanie & Motor
    from syncsphere.core.config.settings import settings
    from motor.motor_asyncio import AsyncIOMotorClient
    from beanie import init_beanie
    from syncsphere.ai.infrastructure.documents.execution_document import PromptExecutionDocument
    from syncsphere.tasks.documents import WorkflowExecutionLogDocument
    from syncsphere.workflow.infrastructure.documents.workflow_document import WorkflowDocument

    uri = None
    for attr in ['mongodb_uri', 'mongo_uri', 'MONGODB_URI']:
        if hasattr(settings, attr):
            uri = str(getattr(settings, attr))
            break
    if not uri:
        for attr in dir(settings):
            sub = getattr(settings, attr, None)
            if sub and hasattr(sub, 'uri'): uri = str(sub.uri); break

    client = AsyncIOMotorClient(uri)
    db = client.syncsphere
    await init_beanie(database=db, document_models=[PromptExecutionDocument, WorkflowExecutionLogDocument, WorkflowDocument])

    from syncsphere.observability.application.services.analytics import AIAnalyticsEngine, ConnectorAnalyticsEngine, RuntimeAnalytics
    
    # Mock repos
    class MockRepo: pass
    
    ai = AIAnalyticsEngine(MockRepo(), MockRepo())
    conn = ConnectorAnalyticsEngine(MockRepo(), MockRepo())
    rt = RuntimeAnalytics(MockRepo())
    
    org_id = 'test_org'
    
    print('--- AI ---')
    ai_data = await ai.get_ai_analytics(org_id)
    print(json.dumps(ai_data, indent=2))
    
    print('--- CONN ---')
    conn_data = await conn.get_connector_analytics(org_id)
    print(json.dumps({k: v for k, v in conn_data.items() if k != 'chart_data'}, indent=2))
    
    print('--- RUNTIME ---')
    rt_data = await rt.get_runtime_stats(org_id)
    print(json.dumps({k: v for k, v in rt_data.items() if k != 'chart_data'}, indent=2))

asyncio.run(run_test())

