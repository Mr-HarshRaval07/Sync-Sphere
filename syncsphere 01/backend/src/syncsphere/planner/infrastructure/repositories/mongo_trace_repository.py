from typing import Optional, List
from syncsphere.planner.domain.entities.trace import PlannerTrace
from syncsphere.planner.domain.repositories.trace import PlannerTraceRepository
from syncsphere.planner.infrastructure.documents.trace_document import PlannerTraceDocument
from syncsphere.planner.infrastructure.mappers import PlannerMappers

class MongoPlannerTraceRepository(PlannerTraceRepository):
    """MongoDB implementation of the PlannerTraceRepository using Beanie ODM."""
    
    async def save(self, trace: PlannerTrace) -> None:
        doc = PlannerMappers.trace_to_document(trace)
        existing = await PlannerTraceDocument.get(trace.id) if trace.id else None
        if existing:
            doc.created_at = existing.created_at
            await existing.update({"$set": {
                "phases": doc.phases,
                "status": doc.status,
                "error_message": doc.error_message,
                "duration_ms": doc.duration_ms,
                "updated_at": doc.updated_at
            }})
        else:
            await doc.insert()
            trace.id = str(doc.id)

    async def get_by_id(self, trace_id: str) -> Optional[PlannerTrace]:
        doc = await PlannerTraceDocument.get(trace_id)
        if doc:
            return PlannerMappers.document_to_trace(doc)
        return None

    async def list_by_session(self, session_id: str) -> List[PlannerTrace]:
        docs = await PlannerTraceDocument.find(
            PlannerTraceDocument.session_id == session_id
        ).to_list()
        return [PlannerMappers.document_to_trace(d) for d in docs]
