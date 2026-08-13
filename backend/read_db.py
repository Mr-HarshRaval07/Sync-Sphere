import motor.motor_asyncio
import asyncio

async def run():
    client = motor.motor_asyncio.AsyncIOMotorClient('mongodb://localhost:27017')
    db = client['syncsphere']
    
    providers = await db.model_providers.find().to_list(100)
    models = await db.models.find().to_list(100)
    
    print("Found Providers:")
    for p in providers:
        print(f" - {p.get('name')} (ID: {p.get('_id')})")
        if p.get('name') == 'gemini':
            await db.model_providers.update_one({'_id': p['_id']}, {'$set': {'name': 'openrouter'}})
            print("   -> Migrated provider to openrouter!")
            
    print("\nFound Models:")
    updated_models = False
    for m in models:
        print(f" - {m.get('name')} (Provider ID: {m.get('provider_id')})")
        if 'gemini' in str(m.get('name')).lower() and m.get('provider_id') != 'openrouter_provider_id': # rough guess
            await db.models.update_one({'_id': m['_id']}, {'$set': {'name': 'inclusionai/ling-3.0-flash:free'}})
            print("   -> Migrated model name to inclusionai/ling-3.0-flash:free!")
            updated_models = True

asyncio.run(run())
