import motor.motor_asyncio
import asyncio

async def run():
    client = motor.motor_asyncio.AsyncIOMotorClient('mongodb://localhost:27017')
    db = client['syncsphere']
    
    providers = await db.ai_model_providers.find().to_list(100)
    models = await db.ai_models.find().to_list(100)
    
    print("Found Providers:", providers)
    print("\nFound Models:", models)
    
    # Delete everything just to force a clean env override
    await db.ai_model_providers.delete_many({})
    await db.ai_models.delete_many({})
    print("Wiped DB models/providers to force environment defaults.")

asyncio.run(run())
