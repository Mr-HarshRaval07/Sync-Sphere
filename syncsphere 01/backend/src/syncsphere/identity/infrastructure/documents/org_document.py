from beanie import Document
from pydantic import Field
from typing import Dict, Any
from datetime import datetime

class OrgDocument(Document):
    """Beanie ODM representation of the Organization aggregate root."""
    name: str = Field(..., description="Organization name")
    slug: str = Field(..., description="URL safe slug key")
    billing_tier: str = Field(default="FREE", description="Subscription plan billing tier")
    quotas: Dict[str, int] = Field(default_factory=dict, description="Resource limits and quotas")
    settings: Dict[str, Any] = Field(default_factory=dict, description="Organization specific configs")
    feature_flags: Dict[str, bool] = Field(default_factory=dict, description="Enabled product features")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "organizations"
        indexes = [
            "slug"
        ]
