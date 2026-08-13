import logging
from typing import Dict

logger = logging.getLogger("syncsphere.runtime.application.services.resource")

class ResourceManager:
    """
    Tracks workers leases, execution slot capacity, memory thresholds, and concurrency counters
    to prevent runner node starvation or resource exhaustion.
    """
    
    def __init__(self, max_concurrency: int = 50, max_queue_capacity: int = 500) -> None:
        self.max_concurrency = max_concurrency
        self.max_queue_capacity = max_queue_capacity
        self.active_slots: Dict[str, int] = {}  # Tracks running threads per tenant org

    async def acquire_slot(self, org_id: str) -> bool:
        """Attempts to claim an execution slot under the tenant's concurrency quota."""
        current = self.active_slots.get(org_id, 0)
        if current >= self.max_concurrency:
            logger.warning("Org '%s' has exceeded its maximum execution concurrency quota.", org_id)
            return False
            
        self.active_slots[org_id] = current + 1
        return True

    async def release_slot(self, org_id: str) -> None:
        """Releases a claimed concurrency execution slot."""
        current = self.active_slots.get(org_id, 0)
        if current > 0:
            self.active_slots[org_id] = current - 1

    def get_active_slots_count(self, org_id: str) -> int:
        return self.active_slots.get(org_id, 0)

    async def check_memory_usage(self) -> float:
        """Simulates memory usage polling (returns a percentage between 0.0 and 1.0)."""
        # In a real environment we could use psutil to poll memory usage
        return 0.45
