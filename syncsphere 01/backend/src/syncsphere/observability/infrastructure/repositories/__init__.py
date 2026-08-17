from typing import List, Optional, Any
from syncsphere.observability.domain.entities.trace import Trace
from syncsphere.observability.domain.entities.replay import ExecutionReplay, WorkflowReplay, PlannerReplay
from syncsphere.observability.domain.entities.log import StructuredLog
from syncsphere.observability.domain.entities.metric_series import MetricSeries
from syncsphere.observability.domain.entities.alert import Alert
from syncsphere.observability.domain.entities.health import HealthCheck
from syncsphere.observability.domain.entities.event_store import EventStoreEntry

from syncsphere.observability.domain.repositories import (
    TraceRepository,
    ReplayRepository,
    MetricRepository,
    AlertRepository,
    HealthRepository,
    LogRepository,
    EventStoreRepository
)
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

from syncsphere.observability.infrastructure.mappers import (
    TraceMapper,
    ReplayMapper,
    MetricMapper,
    AlertMapper,
    HealthMapper,
    LogMapper,
    EventStoreMapper
)

class MongoTraceRepository(TraceRepository):
    async def save(self, trace: Trace) -> None:
        doc = TraceMapper.to_document(trace)
        existing = await TraceDocument.find_one(
            TraceDocument.org_id == trace.org_id,
            TraceDocument.correlation_id == trace.correlation_id
        )
        if existing:
            doc.id = existing.id
            await doc.replace()
        else:
            await doc.insert()
        trace.id = str(doc.id)

    async def get_by_correlation_id(self, org_id: str, correlation_id: str) -> Optional[Trace]:
        doc = await TraceDocument.find_one(
            TraceDocument.org_id == org_id,
            TraceDocument.correlation_id == correlation_id
        )
        return TraceMapper.to_entity(doc) if doc else None

    async def list_by_org(self, org_id: str, limit: int = 100) -> List[Trace]:
        docs = await TraceDocument.find(TraceDocument.org_id == org_id).limit(limit).to_list()
        return [TraceMapper.to_entity(d) for d in docs]


class MongoReplayRepository(ReplayRepository):
    async def save_execution_replay(self, replay: ExecutionReplay) -> None:
        doc = ReplayMapper.to_execution_document(replay)
        existing = await ExecutionReplayDocument.find_one(
            ExecutionReplayDocument.org_id == replay.org_id,
            ExecutionReplayDocument.session_id == replay.session_id
        )
        if existing:
            doc.id = existing.id
            await doc.replace()
        else:
            await doc.insert()
        replay.id = str(doc.id)

    async def get_execution_replay(self, org_id: str, session_id: str) -> Optional[ExecutionReplay]:
        doc = await ExecutionReplayDocument.find_one(
            ExecutionReplayDocument.org_id == org_id,
            ExecutionReplayDocument.session_id == session_id
        )
        return ReplayMapper.to_execution_entity(doc) if doc else None

    async def save_workflow_replay(self, replay: WorkflowReplay) -> None:
        doc = ReplayMapper.to_workflow_document(replay)
        existing = await WorkflowReplayDocument.find_one(
            WorkflowReplayDocument.org_id == replay.org_id,
            WorkflowReplayDocument.workflow_id == replay.workflow_id
        )
        if existing:
            doc.id = existing.id
            await doc.replace()
        else:
            await doc.insert()
        replay.id = str(doc.id)

    async def get_workflow_replay(self, org_id: str, workflow_id: str) -> Optional[WorkflowReplay]:
        doc = await WorkflowReplayDocument.find_one(
            WorkflowReplayDocument.org_id == org_id,
            WorkflowReplayDocument.workflow_id == workflow_id
        )
        return ReplayMapper.to_workflow_entity(doc) if doc else None

    async def save_planner_replay(self, replay: PlannerReplay) -> None:
        doc = ReplayMapper.to_planner_document(replay)
        existing = await PlannerReplayDocument.find_one(
            PlannerReplayDocument.org_id == replay.org_id,
            PlannerReplayDocument.planner_session_id == replay.planner_session_id
        )
        if existing:
            doc.id = existing.id
            await doc.replace()
        else:
            await doc.insert()
        replay.id = str(doc.id)

    async def get_planner_replay(self, org_id: str, planner_session_id: str) -> Optional[PlannerReplay]:
        doc = await PlannerReplayDocument.find_one(
            PlannerReplayDocument.org_id == org_id,
            PlannerReplayDocument.planner_session_id == planner_session_id
        )
        return ReplayMapper.to_planner_entity(doc) if doc else None


class MongoMetricRepository(MetricRepository):
    async def save_series(self, series: MetricSeries) -> None:
        doc = MetricMapper.to_series_document(series)
        existing = await MetricSeriesDocument.find_one(
            MetricSeriesDocument.org_id == series.org_id,
            MetricSeriesDocument.metric_name == series.metric_name
        )
        if existing:
            doc.id = existing.id
            await doc.replace()
        else:
            await doc.insert()
        series.id = str(doc.id)

    async def get_series(self, org_id: str, metric_name: str, start_time: Optional[Any] = None, end_time: Optional[Any] = None) -> Optional[MetricSeries]:
        doc = await MetricSeriesDocument.find_one(
            MetricSeriesDocument.org_id == org_id,
            MetricSeriesDocument.metric_name == metric_name
        )
        if not doc:
            return None
        entity = MetricMapper.to_series_entity(doc)
        if start_time:
            entity.metrics = [m for m in entity.metrics if m.timestamp >= start_time]
        if end_time:
            entity.metrics = [m for m in entity.metrics if m.timestamp <= end_time]
        return entity

    async def list_metric_names(self, org_id: str) -> List[str]:
        docs = await MetricSeriesDocument.find(MetricSeriesDocument.org_id == org_id).to_list()
        return [d.metric_name for d in docs]


class MongoAlertRepository(AlertRepository):
    async def save(self, alert: Alert) -> None:
        doc = AlertMapper.to_document(alert)
        if alert.id:
            existing = await AlertDocument.find_one(AlertDocument.id == alert.id)
            if existing:
                doc.id = existing.id
                await doc.replace()
                return
        await doc.insert()
        alert.id = str(doc.id)

    async def get_by_id(self, org_id: str, alert_id: str) -> Optional[Alert]:
        doc = await AlertDocument.find_one(AlertDocument.org_id == org_id, AlertDocument.id == alert_id)
        return AlertMapper.to_entity(doc) if doc else None

    async def list_active(self, org_id: str) -> List[Alert]:
        docs = await AlertDocument.find(AlertDocument.org_id == org_id, AlertDocument.status == "ACTIVE").to_list()
        return [AlertMapper.to_entity(d) for d in docs]

    async def list_all(self, org_id: str, limit: int = 100) -> List[Alert]:
        docs = await AlertDocument.find(AlertDocument.org_id == org_id).limit(limit).to_list()
        return [AlertMapper.to_entity(d) for d in docs]


class MongoHealthRepository(HealthRepository):
    async def save(self, check: HealthCheck) -> None:
        doc = HealthMapper.to_document(check)
        # Ensure the document id is None before insert to avoid Beanie
        # trying to validate a UUID string as PydanticObjectId
        doc.id = None
        await doc.insert()
        check.id = str(doc.id)

    async def get_latest(self, org_id: str) -> Optional[HealthCheck]:
        doc = await HealthCheckDocument.find(HealthCheckDocument.org_id == org_id).sort("-created_at").first_or_none()
        return HealthMapper.to_entity(doc) if doc else None


class MongoLogRepository(LogRepository):
    async def save(self, log: StructuredLog) -> None:
        doc = LogMapper.to_document(log)
        doc.id = None
        await doc.insert()
        log.id = str(doc.id)

    async def list_logs(self, org_id: str, correlation_id: Optional[str] = None, level: Optional[str] = None, limit: int = 100) -> List[StructuredLog]:
        query = {"org_id": org_id}
        if correlation_id:
            query["correlation_id"] = correlation_id
        if level:
            query["level"] = level
        docs = await StructuredLogDocument.find(query).limit(limit).to_list()
        return [LogMapper.to_entity(d) for d in docs]


class MongoEventStoreRepository(EventStoreRepository):
    async def save(self, entry: EventStoreEntry) -> None:
        doc = EventStoreMapper.to_document(entry)
        doc.id = None
        await doc.insert()
        entry.id = str(doc.id)

    async def get_by_id(self, org_id: str, event_id: str) -> Optional[EventStoreEntry]:
        doc = await EventStoreEntryDocument.find_one(
            EventStoreEntryDocument.org_id == org_id,
            EventStoreEntryDocument.event_id == event_id
        )
        return EventStoreMapper.to_entity(doc) if doc else None

    async def search(self, org_id: str, event_type: Optional[str] = None, correlation_id: Optional[str] = None, limit: int = 100) -> List[EventStoreEntry]:
        query = {"org_id": org_id}
        if event_type:
            query["event_type"] = event_type
        if correlation_id:
            query["correlation_id"] = correlation_id
        docs = await EventStoreEntryDocument.find(query).limit(limit).to_list()
        return [EventStoreMapper.to_entity(d) for d in docs]
