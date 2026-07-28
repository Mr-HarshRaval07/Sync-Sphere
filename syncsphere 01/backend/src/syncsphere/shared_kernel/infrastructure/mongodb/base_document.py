from datetime import datetime
from typing import Optional, Any
from pydantic import Field
from beanie import Document
from pymongo import IndexModel, ASCENDING

class BaseTenantDocument(Document):
    """
    Base document structure for all multi-tenant MongoDB documents in SyncSphere.
    Automatically manages tenancy via org_id, as well as audit timestamps.
    """
    org_id: str = Field(..., description="Organization/Tenant ID partitioning the data")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Time of creation")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Time of last modification")
    deleted_at: Optional[datetime] = Field(default=None, description="Time of soft deletion if applicable")

    async def save(self, *args: Any, **kwargs: Any) -> Any:
        """Overrides save to automatically update updated_at timestamp."""
        self.updated_at = datetime.utcnow()
        return await super().save(*args, **kwargs)

    async def replace(self, *args: Any, **kwargs: Any) -> Any:
        """Overrides replace to automatically update updated_at timestamp."""
        self.updated_at = datetime.utcnow()
        return await super().replace(*args, **kwargs)

    class Settings:
        """Beanie configuration options for indexes."""
        indexes = [
            IndexModel([("org_id", ASCENDING)], name="tenant_isolation_idx"),
            IndexModel([("org_id", ASCENDING), ("deleted_at", ASCENDING)], name="tenant_soft_delete_idx")
        ]
