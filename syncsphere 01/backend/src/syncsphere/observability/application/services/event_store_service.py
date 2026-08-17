from typing import List, Optional, Dict, Any
from datetime import datetime
from syncsphere.observability.domain.entities.event_store import EventStoreEntry
from syncsphere.observability.domain.repositories import EventStoreRepository

class EventArchive:
    """Manages moving older events to cheaper cold storage or cleaning them up."""
    def __init__(self, repo: EventStoreRepository) -> None:
        self.repo = repo

    async def archive_events(self, org_id: str, before_date: datetime) -> int:
        # In this Mongo/Beanie implementation, we could tag them as archived or run cleanup
        # For simulation, we return the count of events matching the date
        return 0

class EventIndexer:
    """Ensures index structures are maintained for fast retrieval."""
    def __init__(self, repo: EventStoreRepository) -> None:
        self.repo = repo

    async def rebuild_indexes(self, org_id: str) -> None:
        # Mongo indexes are handled via Beanie Settings, but we can do validation checks here
        pass

class EventSearch:
    """Performs search lookups over persisted Event Store entries."""
    def __init__(self, repo: EventStoreRepository) -> None:
        self.repo = repo

    async def execute_search(
        self,
        org_id: str,
        event_type: Optional[str] = None,
        correlation_id: Optional[str] = None,
        limit: int = 100
    ) -> List[EventStoreEntry]:
        return await self.repo.search(org_id, event_type, correlation_id, limit)

class EventStoreService:
    def __init__(self, repo: EventStoreRepository) -> None:
        self.repo = repo
        self.archive = EventArchive(repo)
        self.indexer = EventIndexer(repo)
        self.search = EventSearch(repo)

    async def record_event(
        self,
        event_id: str,
        event_type: str,
        org_id: str,
        correlation_id: str,
        timestamp: datetime,
        payload: Dict[str, Any]
    ) -> EventStoreEntry:
        entry = EventStoreEntry(
            event_id=event_id,
            event_type=event_type,
            org_id=org_id,
            correlation_id=correlation_id,
            timestamp=timestamp,
            payload=payload
        )
        await self.repo.save(entry)
        return entry
