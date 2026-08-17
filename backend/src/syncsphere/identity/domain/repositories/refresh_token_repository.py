from abc import ABC, abstractmethod
from typing import Optional
from syncsphere.identity.domain.entities.refresh_token import RefreshToken

class RefreshTokenRepository(ABC):
    """Abstract Repository interface defining persistence operations for RefreshToken entity."""
    
    @abstractmethod
    async def save(self, token: RefreshToken) -> None:
        """Saves or updates RefreshToken state in persistence."""
        pass

    @abstractmethod
    async def get_by_hash(self, token_hash: str) -> Optional[RefreshToken]:
        """Retrieves a RefreshToken by its unique secure hash string."""
        pass

    @abstractmethod
    async def revoke_all_for_user(self, user_id: str) -> None:
        """Revokes all active refresh tokens/sessions belonging to a user (e.g. on compromised rotation)."""
        pass
