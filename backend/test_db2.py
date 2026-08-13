import asyncio, sys, warnings
warnings.filterwarnings('ignore')
sys.path.insert(0, 'src')

async def check():
    from syncsphere.core.config.settings import settings
    from motor.motor_asyncio import AsyncIOMotorClient
    
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
    
    docs = await db.workflow_execution_logs.find({}).to_list(20)
    for d in docs:
        print(f"Status: {d.get('status')}")

asyncio.run(check())
