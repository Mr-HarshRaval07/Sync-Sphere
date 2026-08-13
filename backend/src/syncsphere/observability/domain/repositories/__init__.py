from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from syncsphere.observability.domain.entities.trace import Trace, TraceSpan
from syncsphere.observability.domain.entities.replay import ExecutionReplay, WorkflowReplay, PlannerReplay
from syncsphere.observability.domain.entities.log import StructuredLog
from syncsphere.observability.domain.entities.metric_series import MetricSeries
from syncsphere.observability.domain.entities.alert import Alert
from syncsphere.observability.domain.entities.health import HealthCheck
from syncsphere.observability.domain.entities.event_store import EventStoreEntry

class TraceRepository(ABC):
    @abstractmethod
    async def save(self, trace: Trace) -> None:
        pass

    @abstractmethod
    async def get_by_correlation_id(self, org_id: str, correlation_id: str) -> Optional[Trace]:
        pass

    @abstractmethod
    async def list_by_org(self, org_id: str, limit: int = 100) -> List[Trace]:
        pass

class ReplayRepository(ABC):
    @abstractmethod
    async def save_execution_replay(self, replay: ExecutionReplay) -> None:
        pass

    @abstractmethod
    async def get_execution_replay(self, org_id: str, session_id: str) -> Optional[ExecutionReplay]:
        pass

    @abstractmethod
    async def save_workflow_replay(self, replay: WorkflowReplay) -> None:
        pass

    @abstractmethod
    async def get_workflow_replay(self, org_id: str, workflow_id: str) -> Optional[WorkflowReplay]:
        pass

    @abstractmethod
    async def save_planner_replay(self, replay: PlannerReplay) -> None:
        pass

    @abstractmethod
    async def get_planner_replay(self, org_id: str, planner_session_id: str) -> Optional[PlannerReplay]:
        pass

class MetricRepository(ABC):
    @abstractmethod
    async def save_series(self, series: MetricSeries) -> None:
        pass

    @abstractmethod
    async def get_series(self, org_id: str, metric_name: str, start_time: Optional[Any] = None, end_time: Optional[Any] = None) -> Optional[MetricSeries]:
        pass

    @abstractmethod
    async def list_metric_names(self, org_id: str) -> List[str]:
        pass

class AlertRepository(ABC):
    @abstractmethod
    async def save(self, alert: Alert) -> None:
        pass

    @abstractmethod
    async def get_by_id(self, org_id: str, alert_id: str) -> Optional[Alert]:
        pass

    @abstractmethod
    async def list_active(self, org_id: str) -> List[Alert]:
        pass

    @abstractmethod
    async def list_all(self, org_id: str, limit: int = 100) -> List[Alert]:
        pass

class HealthRepository(ABC):
    @abstractmethod
    async def save(self, check: HealthCheck) -> None:
        pass

    @abstractmethod
    async def get_latest(self, org_id: str) -> Optional[HealthCheck]:
        pass

class LogRepository(ABC):
    @abstractmethod
    async def save(self, log: StructuredLog) -> None:
        pass

    @abstractmethod
    async def list_logs(self, org_id: str, correlation_id: Optional[str] = None, level: Optional[str] = None, limit: int = 100) -> List[StructuredLog]:
        pass

class EventStoreRepository(ABC):
    @abstractmethod
    async def save(self, entry: EventStoreEntry) -> None:
        pass

    @abstractmethod
    async def get_by_id(self, org_id: str, event_id: str) -> Optional[EventStoreEntry]:
        pass

    @abstractmethod
    async def search(self, org_id: str, event_type: Optional[str] = None, correlation_id: Optional[str] = None, limit: int = 100) -> List[EventStoreEntry]:
        pass
