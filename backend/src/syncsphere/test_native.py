import asyncio
import os
import json
from motor.motor_asyncio import AsyncIOMotorClient

# Setup minimal env for beanie
os.environ["HTTP_PORT"] = "8000"
os.environ["MONGODB_URI"] = "mongodb://localhost:27017"

from syncsphere.ai.application.services.ai_gateway_impl import AIGatewayImpl
from syncsphere.ai.infrastructure.repositories.mongo_model_repository import MongoModelRepository, MongoModelProviderRepository
from syncsphere.ai.infrastructure.repositories.mongo_execution_repository import MongoPromptExecutionRepository
from syncsphere.core.providers.secret import KmsSecretProvider
from syncsphere.ai.domain.value_objects import ModelSelectionPolicy, StructuredOutputSchema
from syncsphere.ai.infrastructure.providers.openrouter import OpenRouterProviderAdapter
# pyrefly: ignore [missing-import]
from syncsphere.shared_kernel.infrastructure.mongodb.database import init_db
class DummyEventBus:
    async def publish(self, event):
        pass

async def test_gateway():
    
    await init_db()
    
    # We need an org_id
    org_id = "org_01HFWJ6VDBP7A5N8G1Q9Z2" # typical test org
    
    model_repo = MongoModelRepository()
    provider_repo = MongoModelProviderRepository()
    exec_repo = MongoPromptExecutionRepository()
    secret_prov = KmsSecretProvider()
    
    registry = {
        "openrouter": OpenRouterProviderAdapter()
    }
    
    gateway = AIGatewayImpl(
        model_repo=model_repo,
        provider_repo=provider_repo,
        execution_repo=exec_repo,
        secret_provider=secret_prov,
        event_bus=DummyEventBus(),
        provider_registry=registry
    )
    
    messages = [{"role": "user", "content": "What is 2+2?"}]
    schema = StructuredOutputSchema(
        schema_name="math",
        json_schema={"type": "object", "properties": {"result": {"type": "number"}}}
    )
    
    print("Executing AI...")
    try:
        res = await gateway.structured_output(
            org_id=org_id,
            messages=messages,
            schema=schema,
            policy=ModelSelectionPolicy.FAST
        )
        print(res)
    except Exception as e:
        print(f"Error: {e}")

asyncio.run(test_gateway())
