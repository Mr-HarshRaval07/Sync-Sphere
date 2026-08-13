from typing import Optional, List
from syncsphere.runtime.domain.entities.session import ExecutionSession
from syncsphere.runtime.domain.repositories.session import ExecutionSessionRepository
from syncsphere.runtime.domain.value_objects import ExecutionState
from syncsphere.runtime.infrastructure.documents.session_document import ExecutionSessionDocument
from syncsphere.runtime.infrastructure.mappers import ExecutionSessionMapper

class MongoExecutionSessionRepository(ExecutionSessionRepository):
    """Production Mongo/Beanie implementation of the ExecutionSessionRepository."""
    
    async def save(self, session: ExecutionSession) -> None:
        doc = ExecutionSessionMapper.to_document(session)
        # Check if exists to determine insert vs save update
        existing = await ExecutionSessionDocument.get(doc.id)
        if existing:
            # Transfer properties and save
            await existing.update({"$set": doc.model_dump(exclude={"id"})})
        else:
            await doc.insert()

    async def get_by_id(self, session_id: str) -> Optional[ExecutionSession]:
        doc = await ExecutionSessionDocument.get(session_id)
        if not doc:
            return None
        return ExecutionSessionMapper.to_entity(doc)

    async def list_active(self) -> List[ExecutionSession]:
        active_states = [
            ExecutionState.CREATED,
            ExecutionState.QUEUED,
            ExecutionState.RUNNING,
            ExecutionState.RETRYING,
            ExecutionState.COMPENSATING,
            ExecutionState.AWAITING_APPROVAL
        ]
        docs = await ExecutionSessionDocument.find(
            ExecutionSessionDocument.status.in_(active_states)
        ).to_list()
        return [ExecutionSessionMapper.to_entity(d) for d in docs]
