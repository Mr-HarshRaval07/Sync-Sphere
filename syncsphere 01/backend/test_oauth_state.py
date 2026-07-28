import asyncio
import sys
sys.path.append('src')

from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from syncsphere.tasks.documents import OAuthStateDocument

async def main():
    client = AsyncIOMotorClient('mongodb://localhost:27017')
    await init_beanie(database=client.syncsphere, document_models=[OAuthStateDocument])
    docs = await OAuthStateDocument.find_all().to_list()
    print("OAUTH STATES IN DB:")
    for d in docs:
        print(d.dict())

asyncio.run(main())
