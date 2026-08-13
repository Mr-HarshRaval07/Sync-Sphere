from pydantic import Field
from typing import Optional
from datetime import datetime
from syncsphere.shared_kernel.infrastructure.mongodb.base_document import BaseTenantDocument

class DeveloperApiKeyDocument(BaseTenantDocument):
    """Beanie ODM representation of Developer ApiKey entity."""
    user_id: str = Field(..., description="Creator user identifier link")
    name: str = Field(..., description="API key name description")
    key_hash: str = Field(..., description="SHA-256 secure hash string")
    key_prefix: str = Field(..., description="Client visible key prefix sk_live_xxxx")
    last_used_at: Optional[datetime] = Field(default=None, description="Last successful usage timestamp")
    expires_at: Optional[datetime] = Field(default=None, description="Expiration deadline time")
    status: str = Field(default="ACTIVE", description="ACTIVE or REVOKED")

    class Settings:
        name = "developer_api_keys"
        indexes = [
            "org_id",
            "key_hash",
            "user_id"
        ]
