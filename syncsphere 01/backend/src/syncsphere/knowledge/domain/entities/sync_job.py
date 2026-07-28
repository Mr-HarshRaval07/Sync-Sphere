from datetime import datetime
from typing import Optional
from syncsphere.shared_kernel.domain.entity import Entity

class ConnectorSyncJob(Entity):
    """
    ConnectorSyncJob tracks the background replication processes connecting external systems
    (like Jira, Slack, or databases) to the knowledge platform index.
    """
    
    def __init__(
        self,
        org_id: str,
        source_id: str,
        sync_type: str,  # incremental, webhook, scheduled
        status: str = "queued",  # queued, running, completed, failed
        connector_id: Optional[str] = None,
        records_synced: int = 0,
        error_message: Optional[str] = None,
        started_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None,
        id: Optional[str] = None,
        **kwargs
    ) -> None:
        super().__init__(id=id, **kwargs)
        self.org_id = org_id
        self.source_id = source_id
        self.sync_type = sync_type
        self.status = status
        self.connector_id = connector_id
        self.records_synced = records_synced
        self.error_message = error_message
        self.started_at = started_at or datetime.utcnow()
        self.completed_at = completed_at

    def start(self) -> None:
        self.status = "running"
        self.updated_at = datetime.utcnow()

    def complete(self, records_count: int) -> None:
        self.status = "completed"
        self.records_synced = records_count
        self.completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def fail(self, error: str) -> None:
        self.status = "failed"
        self.error_message = error
        self.completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
