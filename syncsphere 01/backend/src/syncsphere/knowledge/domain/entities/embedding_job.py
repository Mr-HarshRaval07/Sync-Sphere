from datetime import datetime
from typing import Optional
from syncsphere.shared_kernel.domain.entity import Entity

class EmbeddingJob(Entity):
    """
    EmbeddingJob tracks progress on bulk vector generation pipelines,
    identifying completion percentages and transient provider faults.
    """
    
    def __init__(
        self,
        org_id: str,
        source_id: str,
        status: str = "queued",  # queued, running, completed, failed
        total_chunks: int = 0,
        completed_chunks: int = 0,
        error_message: Optional[str] = None,
        started_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None,
        id: Optional[str] = None,
        **kwargs
    ) -> None:
        super().__init__(id=id, **kwargs)
        self.org_id = org_id
        self.source_id = source_id
        self.status = status
        self.total_chunks = total_chunks
        self.completed_chunks = completed_chunks
        self.error_message = error_message
        self.started_at = started_at or datetime.utcnow()
        self.completed_at = completed_at

    def start(self, total: int) -> None:
        self.status = "running"
        self.total_chunks = total
        self.updated_at = datetime.utcnow()

    def update_progress(self, completed: int) -> None:
        self.completed_chunks = completed
        self.updated_at = datetime.utcnow()

    def complete(self) -> None:
        self.status = "completed"
        self.completed_chunks = self.total_chunks
        self.completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def fail(self, error: str) -> None:
        self.status = "failed"
        self.error_message = error
        self.completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
