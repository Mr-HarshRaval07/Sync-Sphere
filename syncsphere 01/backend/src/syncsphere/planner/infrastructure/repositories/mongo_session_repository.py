from typing import Optional
from syncsphere.planner.domain.entities.session import PlanningSession
from syncsphere.planner.domain.repositories.session import PlanningSessionRepository
from syncsphere.planner.infrastructure.documents.session_document import PlanningSessionDocument
from syncsphere.planner.infrastructure.mappers import PlannerMappers

class MongoPlanningSessionRepository(PlanningSessionRepository):
    """MongoDB implementation of the PlanningSessionRepository using Beanie ODM."""
    
    async def save(self, session: PlanningSession) -> None:
        doc = PlannerMappers.session_to_document(session)
        # Check if exists to preserve created_at
        existing = await PlanningSessionDocument.get(session.id) if session.id else None
        if existing:
            doc.created_at = existing.created_at
            # Update Document fields
            await existing.update({"$set": {
                "prompt_history": doc.prompt_history,
                "current_intent": doc.current_intent,
                "current_ast": doc.current_ast,
                "generated_workflow_id": doc.generated_workflow_id,
                "explanation": doc.explanation,
                "metrics": doc.metrics,
                "feedback_history": doc.feedback_history,
                "updated_at": doc.updated_at
            }})
        else:
            await doc.insert()
            session.id = str(doc.id)

    async def get_by_id(self, session_id: str) -> Optional[PlanningSession]:
        doc = await PlanningSessionDocument.get(session_id)
        if doc:
            return PlannerMappers.document_to_session(doc)
        return None
