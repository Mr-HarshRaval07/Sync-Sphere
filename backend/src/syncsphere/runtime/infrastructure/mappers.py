from syncsphere.runtime.domain.entities.session import ExecutionSession
from syncsphere.runtime.domain.entities.trace import ExecutionTrace
from syncsphere.runtime.infrastructure.documents.session_document import ExecutionSessionDocument
from syncsphere.runtime.infrastructure.documents.trace_document import ExecutionTraceDocument

class ExecutionSessionMapper:
    @staticmethod
    def to_document(entity: ExecutionSession) -> ExecutionSessionDocument:
        """Converts an ExecutionSession domain aggregate to its Beanie document counterpart."""
        doc = ExecutionSessionDocument(
            id=entity.id,
            org_id=entity.org_id,
            workflow_id=entity.workflow_id,
            version=entity.version,
            status=entity.status,
            policy=entity.policy,
            variables=entity.variables,
            steps=entity.steps,
            checkpoints=entity.checkpoints,
            metrics=entity.metrics,
            history=entity.history,
            execution_ast=entity.execution_ast,
            error_message=entity.error_message
        )
        return doc

    @staticmethod
    def to_entity(doc: ExecutionSessionDocument) -> ExecutionSession:
        """Converts a Beanie document to its domain ExecutionSession aggregate root counterpart."""
        entity = ExecutionSession(
            id=str(doc.id),
            org_id=doc.org_id,
            workflow_id=doc.workflow_id,
            version=doc.version,
            status=doc.status,
            policy=doc.policy,
            variables=doc.variables,
            steps=doc.steps,
            checkpoints=doc.checkpoints,
            metrics=doc.metrics,
            history=doc.history,
            execution_ast=doc.execution_ast,
            error_message=doc.error_message
        )
        return entity

class ExecutionTraceMapper:
    @staticmethod
    def to_document(entity: ExecutionTrace) -> ExecutionTraceDocument:
        doc = ExecutionTraceDocument(
            id=entity.id,
            org_id=entity.org_id,
            session_id=entity.session_id,
            phases=entity.phases,
            status=entity.status,
            duration_ms=entity.duration_ms
        )
        return doc

    @staticmethod
    def to_entity(doc: ExecutionTraceDocument) -> ExecutionTrace:
        entity = ExecutionTrace(
            id=str(doc.id),
            org_id=doc.org_id,
            session_id=doc.session_id,
            phases=doc.phases,
            status=doc.status,
            duration_ms=doc.duration_ms
        )
        return entity
