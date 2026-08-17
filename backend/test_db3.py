import asyncio, sys, warnings
warnings.filterwarnings('ignore')
sys.path.insert(0, 'src')
async def run():
  from syncsphere.core.config.settings import settings
  from motor.motor_asyncio import AsyncIOMotorClient
  uri = settings.mongodb_uri if hasattr(settings, 'mongodb_uri') else getattr(settings, 'MONGODB_URI', getattr(getattr(settings, 'mongodb', None), 'uri', 'mongodb://localhost:27017'))
  client = AsyncIOMotorClient(uri)
  db = client.syncsphere
  cols = await db.list_collection_names()
  if 'distributed_traces' in cols: 
      c = await db.distributed_traces.count_documents({})
      print('distributed_traces count:', c)
  if 'traces' in cols: 
      c = await db.traces.count_documents({})
      print('traces count:', c)
asyncio.run(run())
