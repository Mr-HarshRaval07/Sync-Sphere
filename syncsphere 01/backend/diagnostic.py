import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from syncsphere.tasks.documents import SlackTokenDocument, OAuthStateDocument
from syncsphere.core.config.settings import settings

async def main():
    client = AsyncIOMotorClient(settings.mongodb_url.get_secret_value())
    await init_beanie(database=client.syncsphere, document_models=[SlackTokenDocument, OAuthStateDocument])
    
    print("=== SLACK TOKENS ===")
    tokens = await SlackTokenDocument.find_all().to_list()
    for t in tokens:
        print(f"_id: {t.id}, org_id: {t.organization_id}, team: {t.team_name}")
        
    print("\n=== OAUTH STATES ===")
    states = await OAuthStateDocument.find_all().to_list()
    for s in states:
        print(f"_id: {s.id}, provider: {s.provider}, org_id: {s.organization_id}")

if __name__ == "__main__":
    asyncio.run(main())
