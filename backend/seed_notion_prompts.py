import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from syncsphere.ai.infrastructure.documents.prompt_document import PromptTemplateDocument, PromptVersionDocument
from pydantic_core import to_json
from syncsphere.core.config.settings import settings
import datetime

async def seed_prompts():
    client = AsyncIOMotorClient(settings.mongodb_uri)
    await client.drop_database("test_prompts_db_init") # just to prevent typing error
    
    # We will just insert them into the real database
    from beanie import init_beanie
    await init_beanie(database=client[settings.mongodb_db_name], document_models=[PromptTemplateDocument])
    
    # Usually org_id is required, we use a placeholder or common dev org ID "org_default" if it exists, or just fetch the first org?
    # Let's just create them for all distinct orgs
    # In a real system, we'd use system defaults or attach to the main user org
    org_id = "org_12345" # Using a mock or finding it via another collection
    
    from syncsphere.identity.infrastructure.documents import OrganizationDocument
    await init_beanie(database=client[settings.mongodb_db_name], document_models=[PromptTemplateDocument, OrganizationDocument])
    orgs = await OrganizationDocument.find_all().to_list()
    if not orgs:
        print("No organizations found to seed")
        return
        
    org_id = orgs[0].id
    
    prompts_to_add = [
        {
            "name": "Create Meeting Notes in Notion",
            "description": "Takes the rough notes and formats them into a professional meeting notes page in Notion.",
            "version": 1,
            "system_template": "You are a professional secretary. Extract action items, attendees, and key decisions from the notes.",
            "user_template": "Extract meeting notes. Here are my raw notes: {{raw_notes}}",
            "variables": [{"name": "raw_notes", "type": "string", "description": "Raw meeting notes and transcripts"}]
        },
        {
            "name": "Create AI Summary",
            "description": "Summarizes a long block of text or discussion and generates an AI Summary page in Notion.",
            "version": 1,
            "system_template": "You are an AI assistant. Analyze the text and generate a concise executive summary.",
            "user_template": "Generate a summary for the following text: {{long_text}}",
            "variables": [{"name": "long_text", "type": "string", "description": "The text to summarize"}]
        }
    ]
    
    for prompt in prompts_to_add:
        existing = await PromptTemplateDocument.find_one({"org_id": str(org_id), "name": prompt["name"]})
        if not existing:
            v = PromptVersionDocument(version=prompt["version"], system_template=prompt["system_template"], user_template=prompt["user_template"], created_at=datetime.datetime.utcnow(), hash="seed")
            doc = PromptTemplateDocument(
                org_id=str(org_id),
                name=prompt["name"],
                description=prompt["description"],
                latest_version=prompt["version"],
                variables=prompt["variables"],
                versions=[v]
            )
            await doc.insert()
            print(f"Inserted prompt {prompt['name']}")

if __name__ == "__main__":
    asyncio.run(seed_prompts())
