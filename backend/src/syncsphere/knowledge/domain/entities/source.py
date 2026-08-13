import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from syncsphere.shared_kernel.domain.entity import Entity
from syncsphere.knowledge.domain.value_objects import (
    KnowledgeSourceType,
    KnowledgePolicy,
    KnowledgeMetadata
)

class KnowledgeSource(Entity):
    """
    KnowledgeSource represents a unified connection or data input channel:
    local file, remote website, database sync, or connector framework tool.
    """
    
    def __init__(
        self,
        org_id: str,
        name: str,
        type: KnowledgeSourceType,
        config: Dict[str, Any],
        policy: Optional[KnowledgePolicy] = None,
        sync_strategy: str = "incremental",  # incremental, webhook, scheduled
        sync_schedule: Optional[str] = None,  # cron pattern
        status: str = "created",  # created, active, syncing, failed
        last_sync_at: Optional[datetime] = None,
        metadata: Optional[KnowledgeMetadata] = None,
        id: Optional[str] = None,
        **kwargs
    ) -> None:
        super().__init__(id=id, **kwargs)
        self.org_id = org_id
        self.name = name
        self.type = type
        self.config = config
        self.policy = policy or KnowledgePolicy()
        self.sync_strategy = sync_strategy
        self.sync_schedule = sync_schedule
        self.status = status
        self.last_sync_at = last_sync_at
        self.metadata = metadata or KnowledgeMetadata()

    def start_sync(self) -> None:
        self.status = "syncing"
        self.updated_at = datetime.utcnow()

    def complete_sync(self) -> None:
        self.status = "active"
        self.last_sync_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def fail_sync(self) -> None:
        self.status = "failed"
        self.updated_at = datetime.utcnow()
