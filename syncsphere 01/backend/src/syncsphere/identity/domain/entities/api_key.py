from datetime import datetime
from typing import List, Optional
from syncsphere.shared_kernel.domain.entity import Entity

class ApiKey(Entity):
    """
    ApiKey domain entity representing a hashed programmatic access credential.
    """
    
    def __init__(
        self,
        org_id: str,
        user_id: str,
        name: str,
        key_hash: str,
        key_prefix: str,
        scopes: List[str],
        expires_at: Optional[datetime] = None,
        status: str = "ACTIVE",
        id: Optional[str] = None,
        **kwargs
    ) -> None:
        super().__init__(id=id, **kwargs)
        self.org_id = org_id
        self.user_id = user_id
        self.name = name
        self.key_hash = key_hash
        self.key_prefix = key_prefix
        self.scopes = scopes
        self.expires_at = expires_at
        self.status = status

    @property
    def is_expired(self) -> bool:
        """Returns True if the expiration date has passed."""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at

    @property
    def is_active(self) -> bool:
        """Returns True if key is ACTIVE and not expired."""
        return self.status == "ACTIVE" and not self.is_expired

    def revoke(self) -> None:
        """Revokes the API Key immediately."""
        self.status = "REVOKED"
