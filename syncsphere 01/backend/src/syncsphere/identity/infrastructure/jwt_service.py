import jwt
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List
from syncsphere.core.config.settings import settings

logger = logging.getLogger("syncsphere.identity.infrastructure.jwt_service")

class JWTService:
    """JWT creation and claim validation service."""

    def __init__(self) -> None:
        self._secret = settings.jwt_secret.get_secret_value()
        self._algorithm = settings.jwt_algorithm
        self._access_ttl = settings.jwt_access_token_ttl

    def create_access_token(self, user_id: str, org_id: str, roles: List[str]) -> str:
        """Generates a short-lived access JWT token."""
        payload = {
            "sub": user_id,
            "org": org_id,
            "roles": roles,
            "type": "access",
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(seconds=self._access_ttl)
        }
        return jwt.encode(payload, self._secret, algorithm=self._algorithm)

    def decode_token(self, token: str) -> Dict[str, Any]:
        """
        Decodes and validates a JWT signature and claims.
        Raises jwt.ExpiredSignatureError or jwt.InvalidTokenError on failure.
        """
        return jwt.decode(token, self._secret, algorithms=[self._algorithm])
