from pydantic import Field
from typing import List, Optional
from datetime import datetime
from syncsphere.shared_kernel.infrastructure.mongodb.base_document import BaseTenantDocument

class ApiKeyDocument(BaseTenantDocument):
    """Beanie ODM representation of ApiKey entity."""
    user_id: str = Field(..., description="Creator user identifier link")
    name: str = Field(..., description="API key name description")
    key_hash: str = Field(..., description="SHA-256 secure hash string")
    key_prefix: str = Field(..., description="Client visible key prefix Sk_live_xxxx")
    scopes: List[str] = Field(default_factory=list, description="Access permissions scope keys")
    expires_at: Optional[datetime] = Field(default=None, description="Expiration deadline time")
    status: str = Field(default="ACTIVE", description="ACTIVE or REVOKED")

    class Settings:
        name = "api_keys"
        indexes = [
            "org_id",
            "key_hash",
            "user_id"
        ]
