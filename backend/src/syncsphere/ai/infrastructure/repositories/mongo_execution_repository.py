from typing import Optional, List
from beanie import PydanticObjectId
from syncsphere.ai.domain.repositories import PromptExecutionRepository
from syncsphere.ai.domain.entities.execution import PromptExecution
from syncsphere.ai.infrastructure.documents import PromptExecutionDocument
from syncsphere.ai.infrastructure.mappers import AIMappers

class MongoPromptExecutionRepository(PromptExecutionRepository):
    """Concrete Mongo repository implementing PromptExecutionRepository using Beanie ODM."""
    async def save(self, execution: PromptExecution) -> None:
        doc = AIMappers.execution_to_document(execution)
        if execution.id:
            try:
                existing = await PromptExecutionDocument.get(PydanticObjectId(execution.id))
                if existing:
                    existing.response_text = doc.response_text
                    existing.latency_ms = doc.latency_ms
                    existing.prompt_tokens = doc.prompt_tokens
                    existing.completion_tokens = doc.completion_tokens
                    existing.total_tokens = doc.total_tokens
                    existing.prompt_cost = doc.prompt_cost
                    existing.completion_cost = doc.completion_cost
                    existing.total_cost = doc.total_cost
                    await existing.save()
                    return
            except Exception:
                pass
        await doc.insert()
        execution.id = str(doc.id)

    async def get_by_id(self, execution_id: str) -> Optional[PromptExecution]:
        try:
            doc = await PromptExecutionDocument.get(PydanticObjectId(execution_id))
            return AIMappers.execution_to_domain(doc) if doc else None
        except Exception:
            return None

    async def list_by_org(self, org_id: str, page: int, page_size: int) -> List[PromptExecution]:
        skip = (page - 1) * page_size
        docs = await PromptExecutionDocument.find({"org_id": org_id}).skip(skip).limit(page_size).to_list()
        return [AIMappers.execution_to_domain(doc) for doc in docs]
