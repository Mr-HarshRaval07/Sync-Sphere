from typing import Optional, List
from beanie import PydanticObjectId
from syncsphere.ai.domain.repositories import AIModelRepository, ModelProviderRepository
from syncsphere.ai.domain.entities.model import AIModel, ModelProvider
from syncsphere.ai.infrastructure.documents import AIModelDocument, ModelProviderDocument
from syncsphere.ai.infrastructure.mappers import AIMappers

class MongoModelProviderRepository(ModelProviderRepository):
    """Concrete Mongo repository implementing ModelProviderRepository using Beanie ODM."""
    async def save(self, provider: ModelProvider) -> None:
        doc = AIMappers.provider_to_document(provider)
        if provider.id:
            try:
                existing = await ModelProviderDocument.get(PydanticObjectId(provider.id))
                if existing:
                    existing.name = doc.name
                    existing.api_key_encrypted = doc.api_key_encrypted
                    existing.api_url_override = doc.api_url_override
                    existing.priority_level = doc.priority_level
                    existing.is_primary = doc.is_primary
                    existing.is_healthy = doc.is_healthy
                    existing.latency_ms = doc.latency_ms
                    existing.error_message = doc.error_message
                    existing.status = doc.status
                    existing.config_meta = doc.config_meta
                    await existing.save()
                    return
            except Exception:
                pass
        await doc.insert()
        provider.id = str(doc.id)

    async def get_by_id(self, provider_id: str) -> Optional[ModelProvider]:
        try:
            doc = await ModelProviderDocument.get(PydanticObjectId(provider_id))
            return AIMappers.provider_to_domain(doc) if doc else None
        except Exception:
            return None

    async def get_by_name(self, org_id: str, name: str) -> Optional[ModelProvider]:
        # Avoid attribute access on Document class in Beanie by using dict match
        doc = await ModelProviderDocument.find_one(
            {"org_id": org_id, "name": name.lower().strip()}
        )
        return AIMappers.provider_to_domain(doc) if doc else None

    async def list_by_org(self, org_id: str) -> List[ModelProvider]:
        docs = await ModelProviderDocument.find({"org_id": org_id}).to_list()
        return [AIMappers.provider_to_domain(doc) for doc in docs]

    async def delete(self, provider_id: str) -> None:
        try:
            doc = await ModelProviderDocument.get(PydanticObjectId(provider_id))
            if doc:
                await doc.delete()
        except Exception:
            pass


class MongoAIModelRepository(AIModelRepository):
    """Concrete Mongo repository implementing AIModelRepository using Beanie ODM."""
    async def save(self, model: AIModel) -> None:
        doc = AIMappers.model_to_document(model)
        if model.id:
            try:
                existing = await AIModelDocument.get(PydanticObjectId(model.id))
                if existing:
                    existing.provider_id = doc.provider_id
                    existing.name = doc.name
                    existing.display_name = doc.display_name
                    existing.capabilities = doc.capabilities
                    existing.context_window = doc.context_window
                    existing.max_output_tokens = doc.max_output_tokens
                    existing.cost_per_1k_input = doc.cost_per_1k_input
                    existing.cost_per_1k_output = doc.cost_per_1k_output
                    existing.status = doc.status
                    await existing.save()
                    return
            except Exception:
                pass
        await doc.insert()
        model.id = str(doc.id)

    async def get_by_id(self, model_id: str) -> Optional[AIModel]:
        try:
            doc = await AIModelDocument.get(PydanticObjectId(model_id))
            return AIMappers.model_to_domain(doc) if doc else None
        except Exception:
            return None

    async def get_by_name(self, org_id: str, name: str) -> Optional[AIModel]:
        doc = await AIModelDocument.find_one({"org_id": org_id, "name": name.strip()})
        return AIMappers.model_to_domain(doc) if doc else None

    async def list_by_org(self, org_id: str) -> List[AIModel]:
        docs = await AIModelDocument.find({"org_id": org_id}).to_list()
        return [AIMappers.model_to_domain(doc) for doc in docs]

    async def delete(self, model_id: str) -> None:
        try:
            doc = await AIModelDocument.get(PydanticObjectId(model_id))
            if doc:
                await doc.delete()
        except Exception:
            pass
