from syncsphere.observability.domain.entities.trace import Trace, TraceSpan
from syncsphere.observability.domain.entities.replay import ExecutionReplay, WorkflowReplay, PlannerReplay
from syncsphere.observability.domain.entities.log import StructuredLog
from syncsphere.observability.domain.entities.metric_series import MetricSeries
from syncsphere.observability.domain.entities.alert import Alert
from syncsphere.observability.domain.entities.health import HealthCheck
from syncsphere.observability.domain.entities.event_store import EventStoreEntry
from syncsphere.observability.domain.value_objects import TraceSpanVO, TimelineEvent, Metric, ServiceStatus

from syncsphere.observability.infrastructure.documents.trace_document import TraceDocument
from syncsphere.observability.infrastructure.documents.replay_document import (
    ExecutionReplayDocument,
    WorkflowReplayDocument,
    PlannerReplayDocument
)
from syncsphere.observability.infrastructure.documents.metric_document import MetricSeriesDocument
from syncsphere.observability.infrastructure.documents.alert_document import AlertDocument
from syncsphere.observability.infrastructure.documents.health_document import HealthCheckDocument
from syncsphere.observability.infrastructure.documents.log_document import StructuredLogDocument
from syncsphere.observability.infrastructure.documents.event_store_document import EventStoreEntryDocument

class TraceMapper:
    @staticmethod
    def to_entity(doc: TraceDocument) -> Trace:
        spans = [
            TraceSpan(
                span_id=s.span_id,
                name=s.name,
                correlation_id=doc.correlation_id,
                parent_span_id=s.parent_span_id,
                status=s.status,
                start_time=s.start_time,
                end_time=s.end_time,
                attributes=s.attributes
            )
            for s in doc.spans
        ]
        return Trace(
            id=str(doc.id),
            org_id=doc.org_id,
            correlation_id=doc.correlation_id,
            spans=spans,
            created_at=doc.created_at,
            updated_at=doc.updated_at
        )

    @staticmethod
    def to_document(entity: Trace) -> TraceDocument:
        spans_vo = [
            TraceSpanVO(
                span_id=s.span_id,
                name=s.name,
                parent_span_id=s.parent_span_id,
                status=s.status,
                start_time=s.start_time,
                end_time=s.end_time,
                attributes=s.attributes
            )
            for s in entity.spans
        ]
        doc = TraceDocument(
            org_id=entity.org_id,
            correlation_id=entity.correlation_id,
            spans=spans_vo,
            created_at=entity.created_at,
            updated_at=entity.updated_at
        )

        return doc

class ReplayMapper:
    @staticmethod
    def to_execution_entity(doc: ExecutionReplayDocument) -> ExecutionReplay:
        return ExecutionReplay(
            id=str(doc.id),
            org_id=doc.org_id,
            session_id=doc.session_id,
            timeline_events=doc.timeline_events,
            created_at=doc.created_at,
            updated_at=doc.updated_at
        )

    @staticmethod
    def to_execution_document(entity: ExecutionReplay) -> ExecutionReplayDocument:
        doc = ExecutionReplayDocument(
            org_id=entity.org_id,
            session_id=entity.session_id,
            timeline_events=entity.timeline_events,
            created_at=entity.created_at,
            updated_at=entity.updated_at
        )

        return doc

    @staticmethod
    def to_workflow_entity(doc: WorkflowReplayDocument) -> WorkflowReplay:
        return WorkflowReplay(
            id=str(doc.id),
            org_id=doc.org_id,
            workflow_id=doc.workflow_id,
            reconstruct_steps=doc.reconstruct_steps,
            created_at=doc.created_at,
            updated_at=doc.updated_at
        )

    @staticmethod
    def to_workflow_document(entity: WorkflowReplay) -> WorkflowReplayDocument:
        doc = WorkflowReplayDocument(
            org_id=entity.org_id,
            workflow_id=entity.workflow_id,
            reconstruct_steps=entity.reconstruct_steps,
            created_at=entity.created_at,
            updated_at=entity.updated_at
        )

        return doc

    @staticmethod
    def to_planner_entity(doc: PlannerReplayDocument) -> PlannerReplay:
        return PlannerReplay(
            id=str(doc.id),
            org_id=doc.org_id,
            planner_session_id=doc.planner_session_id,
            reasoning_cycles=doc.reasoning_cycles,
            created_at=doc.created_at,
            updated_at=doc.updated_at
        )

    @staticmethod
    def to_planner_document(entity: PlannerReplay) -> PlannerReplayDocument:
        doc = PlannerReplayDocument(
            org_id=entity.org_id,
            planner_session_id=entity.planner_session_id,
            reasoning_cycles=entity.reasoning_cycles,
            created_at=entity.created_at,
            updated_at=entity.updated_at
        )

        return doc

class MetricMapper:
    @staticmethod
    def to_series_entity(doc: MetricSeriesDocument) -> MetricSeries:
        return MetricSeries(
            id=str(doc.id),
            org_id=doc.org_id,
            metric_name=doc.metric_name,
            metrics=doc.metrics,
            created_at=doc.created_at,
            updated_at=doc.updated_at
        )

    @staticmethod
    def to_series_document(entity: MetricSeries) -> MetricSeriesDocument:
        doc = MetricSeriesDocument(
            org_id=entity.org_id,
            metric_name=entity.metric_name,
            metrics=entity.metrics,
            created_at=entity.created_at,
            updated_at=entity.updated_at
        )

        return doc

class AlertMapper:
    @staticmethod
    def to_entity(doc: AlertDocument) -> Alert:
        return Alert(
            id=str(doc.id),
            org_id=doc.org_id,
            name=doc.name,
            message=doc.message,
            severity=doc.severity,
            status=doc.status,
            metric_name=doc.metric_name,
            resolved_at=doc.resolved_at,
            created_at=doc.created_at,
            updated_at=doc.updated_at
        )

    @staticmethod
    def to_document(entity: Alert) -> AlertDocument:
        doc = AlertDocument(
            org_id=entity.org_id,
            name=entity.name,
            message=entity.message,
            severity=entity.severity,
            status=entity.status,
            metric_name=entity.metric_name,
            resolved_at=entity.resolved_at,
            created_at=entity.created_at,
            updated_at=entity.updated_at
        )

        return doc

class HealthMapper:
    @staticmethod
    def to_entity(doc: HealthCheckDocument) -> HealthCheck:
        return HealthCheck(
            id=str(doc.id),
            org_id=doc.org_id,
            services=doc.services,
            created_at=doc.created_at,
            updated_at=doc.updated_at
        )

    @staticmethod
    def to_document(entity: HealthCheck) -> HealthCheckDocument:
        # Important: Beanie Document.id/_id must be a real Mongo ObjectId.
        # The domain entity uses string IDs (str(doc.id)), which cannot be
        # assigned back to the Beanie document for new inserts.
        #
        # Therefore we NEVER set HealthCheckDocument.id here.
        doc = HealthCheckDocument(
            org_id=entity.org_id,
            services=entity.services,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )

        return doc

class LogMapper:
    @staticmethod
    def to_entity(doc: StructuredLogDocument) -> StructuredLog:
        return StructuredLog(
            id=str(doc.id),
            org_id=doc.org_id,
            correlation_id=doc.correlation_id,
            message=doc.message,
            level=doc.level,
            module=doc.module,
            timestamp=doc.timestamp,
            context_info=doc.context_info,
            created_at=doc.created_at,
            updated_at=doc.updated_at
        )

    @staticmethod
    def to_document(entity: StructuredLog) -> StructuredLogDocument:
        doc = StructuredLogDocument(
            org_id=entity.org_id,
            correlation_id=entity.correlation_id,
            message=entity.message,
            level=entity.level,
            module=entity.module,
            timestamp=entity.timestamp,
            context_info=entity.context_info,
            created_at=entity.created_at,
            updated_at=entity.updated_at
        )

        return doc

class EventStoreMapper:
    @staticmethod
    def to_entity(doc: EventStoreEntryDocument) -> EventStoreEntry:
        return EventStoreEntry(
            id=str(doc.id),
            event_id=doc.event_id,
            event_type=doc.event_type,
            org_id=doc.org_id,
            correlation_id=doc.correlation_id,
            timestamp=doc.timestamp,
            payload=doc.payload,
            created_at=doc.created_at,
            updated_at=doc.updated_at
        )

    @staticmethod
    def to_document(entity: EventStoreEntry) -> EventStoreEntryDocument:
        doc = EventStoreEntryDocument(
            event_id=entity.event_id,
            event_type=entity.event_type,
            org_id=entity.org_id,
            correlation_id=entity.correlation_id,
            timestamp=entity.timestamp,
            payload=entity.payload,
            created_at=entity.created_at,
            updated_at=entity.updated_at
        )

        return doc
