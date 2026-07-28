import asyncio
import sys
import os
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))
from syncsphere.shared_kernel.infrastructure.mongodb.connection import mongodb_manager

async def dump_ai_db():
    try:
        from syncsphere.tasks.documents import TaskDocument
        await mongodb_manager.connect(document_models=[TaskDocument])
        db = mongodb_manager.db
        
        providers = await db.ai_providers.find({}).to_list(100)
        models = await db.ai_models.find({}).to_list(100)
        
        def stringify(doc):
            if isinstance(doc, list):
                return [stringify(d) for d in doc]
            elif isinstance(doc, dict):
                return {k: str(v) for k, v in doc.items()}
            return str(doc)
            
        result = {
            "providers": stringify(providers),
            "models": stringify(models)
        }
        with open("db_ai_audit.json", "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)
    except Exception as e:
        with open("db_ai_audit.json", "w", encoding="utf-8") as f:
            json.dump({"error": str(e)}, f)
    finally:
        await mongodb_manager.disconnect()

if __name__ == "__main__":
    asyncio.run(dump_ai_db())
