from datetime import datetime
from typing import Optional, Dict
from syncsphere.shared_kernel.domain.entity import Entity

class RefreshToken(Entity):
    """
    RefreshToken domain entity representing an active session token.
    Enforces single-use rotation rules.
    """
    
    def __init__(
        self,
        org_id: str,
        user_id: str,
        token_hash: str,
        expires_at: datetime,
        is_revoked: bool = False,
        replaced_by: Optional[str] = None,
        device_info: Optional[Dict[str, str]] = None,
        id: Optional[str] = None,
        **kwargs
    ) -> None:
        super().__init__(id=id, **kwargs)
        self.org_id = org_id
        self.user_id = user_id
        self.token_hash = token_hash
        self.expires_at = expires_at
        self.is_revoked = is_revoked
        self.replaced_by = replaced_by
        self.device_info = device_info or {}

    @property
    def is_expired(self) -> bool:
        """Checks if expiration timestamp has passed."""
        return datetime.utcnow() > self.expires_at

    @property
    def is_active(self) -> bool:
        """Returns True if the token is active, not revoked, and not expired."""
        return not self.is_revoked and not self.is_expired

    def revoke(self, replaced_by: Optional[str] = None) -> None:
        """Revokes the refresh token and sets rotation successor token ID if provided."""
        self.is_revoked = True
        if replaced_by:
            self.replaced_by = replaced_by
