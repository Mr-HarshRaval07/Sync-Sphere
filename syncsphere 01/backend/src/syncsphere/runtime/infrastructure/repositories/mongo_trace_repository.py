from typing import Optional
from syncsphere.runtime.domain.entities.trace import ExecutionTrace
from syncsphere.runtime.domain.repositories.trace import ExecutionTraceRepository
from syncsphere.runtime.infrastructure.documents.trace_document import ExecutionTraceDocument
from syncsphere.runtime.infrastructure.mappers import ExecutionTraceMapper

class MongoExecutionTraceRepository(ExecutionTraceRepository):
    """Production Mongo/Beanie implementation of the ExecutionTraceRepository."""
    
    async def save(self, trace: ExecutionTrace) -> None:
        doc = ExecutionTraceMapper.to_document(trace)
        existing = await ExecutionTraceDocument.get(doc.id)
        if existing:
            await existing.update({"$set": doc.model_dump(exclude={"id"})})
        else:
            await doc.insert()

    async def get_by_id(self, trace_id: str) -> Optional[ExecutionTrace]:
        doc = await ExecutionTraceDocument.get(trace_id)
        if not doc:
            return None
        return ExecutionTraceMapper.to_entity(doc)

    async def get_by_session(self, session_id: str) -> Optional[ExecutionTrace]:
        doc = await ExecutionTraceDocument.find_one(
            ExecutionTraceDocument.session_id == session_id
        )
        if not doc:
            return None
        return ExecutionTraceMapper.to_entity(doc)
