
import asyncio, sys, warnings
warnings.filterwarnings('ignore')
sys.path.insert(0, 'src')

async def check():
    from syncsphere.core.config.settings import settings
    from motor.motor_asyncio import AsyncIOMotorClient
    
    mongo_uri = None
    for attr in ['mongodb_uri', 'mongo_uri', 'MONGODB_URI']:
        if hasattr(settings, attr):
            mongo_uri = str(getattr(settings, attr))
            break
    if not mongo_uri:
        for attr in dir(settings):
            sub = getattr(settings, attr, None)
            if sub and hasattr(sub, 'uri'): mongo_uri = str(sub.uri); break
    
    db_name = 'syncsphere'
    client = AsyncIOMotorClient(mongo_uri)
    db = client[db_name]
    
    print('==== counts ====')
    print('prompt_executions:', await db.prompt_executions.count_documents({}))
    p = await db.prompt_executions.find_one({}, sort=[('created_at', -1)])
    if p: print('LATEST PROMPT created_at:', p.get('created_at'))
    
    print('workflow_execution_logs:', await db.workflow_execution_logs.count_documents({}))
    w = await db.workflow_execution_logs.find_one({}, sort=[('started_at', -1)])
    if w: print('LATEST WORKFLOW LOG started_at:', w.get('started_at'))

    print('execution_runs:', await db.execution_runs.count_documents({}))
    e = await db.execution_runs.find_one({}, sort=[('started_at', -1)])
    if e: print('LATEST EXECUTION RUN started_at:', e.get('started_at'))

asyncio.run(check())

