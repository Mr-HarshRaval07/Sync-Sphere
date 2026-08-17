from pydantic import Field
from typing import Optional, Dict
from datetime import datetime
from syncsphere.shared_kernel.infrastructure.mongodb.base_document import BaseTenantDocument

class RefreshTokenDocument(BaseTenantDocument):
    """Beanie ODM representation of RefreshToken session entity."""
    user_id: str = Field(..., description="User ID owner of the token session")
    token_hash: str = Field(..., description="SHA-256 secure hash string")
    expires_at: datetime = Field(..., description="Expiration timestamp")
    is_revoked: bool = Field(default=False, description="Flag indicating if token is revoked")
    replaced_by: Optional[str] = Field(default=None, description="Identifier of successor rotation token")
    device_info: Dict[str, str] = Field(default_factory=dict, description="Metadata linking browser/client details")

    class Settings:
        name = "refresh_tokens"
        indexes = [
            "org_id",
            "token_hash",
            "user_id"
        ]
        # Automatic MongoDB TTL cleanup indexing can be mapped here or handled via Beanie.
