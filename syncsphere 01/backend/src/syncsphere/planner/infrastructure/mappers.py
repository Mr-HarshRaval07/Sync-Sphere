from typing import Any
from syncsphere.planner.domain.entities.session import PlanningSession
from syncsphere.planner.domain.entities.trace import PlannerTrace
from syncsphere.planner.domain.value_objects import (
    UserIntent,
    PlanAST,
    PlanningExplanation,
    PlanningMetrics,
    PlannerFeedback
)
from syncsphere.planner.infrastructure.documents.session_document import PlanningSessionDocument
from syncsphere.planner.infrastructure.documents.trace_document import PlannerTraceDocument

class PlannerMappers:
    """Translation mapper between Planner domain aggregates and MongoDB Beanie documents."""
    
    @staticmethod
    def session_to_document(domain: PlanningSession) -> PlanningSessionDocument:
        doc = PlanningSessionDocument(
            id=domain.id,
            org_id=domain.org_id,
            user_id=domain.user_id,
            prompt_history=domain.prompt_history,
            current_intent=domain.current_intent.model_dump() if domain.current_intent else None,
            current_ast=domain.current_ast.model_dump() if domain.current_ast else None,
            generated_workflow_id=domain.generated_workflow_id,
            explanation=domain.explanation.model_dump() if domain.explanation else None,
            metrics=domain.metrics.model_dump() if domain.metrics else None,
            feedback_history=[f.model_dump() for f in domain.feedback_history]
        )
        return doc

    @staticmethod
    def document_to_session(doc: PlanningSessionDocument) -> PlanningSession:
        session = PlanningSession(
            id=str(doc.id) if doc.id else None,
            org_id=doc.org_id,
            user_id=doc.user_id,
            prompt_history=doc.prompt_history,
            current_intent=UserIntent.model_validate(doc.current_intent) if doc.current_intent else None,
            current_ast=PlanAST.model_validate(doc.current_ast) if doc.current_ast else None,
            generated_workflow_id=doc.generated_workflow_id,
            explanation=PlanningExplanation.model_validate(doc.explanation) if doc.explanation else None,
            metrics=PlanningMetrics.model_validate(doc.metrics) if doc.metrics else None,
            feedback_history=[PlannerFeedback.model_validate(f) for f in doc.feedback_history]
        )
        return session

    @staticmethod
    def trace_to_document(domain: PlannerTrace) -> PlannerTraceDocument:
        doc = PlannerTraceDocument(
            id=domain.id,
            org_id=domain.org_id,
            session_id=domain.session_id,
            phases=domain.phases,
            status=domain.status,
            error_message=domain.error_message,
            duration_ms=domain.duration_ms
        )
        return doc

    @staticmethod
    def document_to_trace(doc: PlannerTraceDocument) -> PlannerTrace:
        trace = PlannerTrace(
            id=str(doc.id) if doc.id else None,
            org_id=doc.org_id,
            session_id=doc.session_id,
            phases=doc.phases,
            status=doc.status,
            error_message=doc.error_message,
            duration_ms=doc.duration_ms
        )
        return trace
