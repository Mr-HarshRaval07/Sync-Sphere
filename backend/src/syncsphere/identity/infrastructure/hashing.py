import logging
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

logger = logging.getLogger("syncsphere.identity.infrastructure.hashing")

class PasswordHasherService:
    """Argon2id password hashing and verification implementation."""

    def __init__(self) -> None:
        # Default Argon2id parameters
        self._ph = PasswordHasher(
            time_cost=3,
            memory_cost=65536,
            parallelism=4,
            hash_len=32,
            salt_len=16
        )

    def hash_password(self, password: str) -> str:
        """Generates a secure Argon2id hash of a password string."""
        return self._ph.hash(password)

    def verify_password(self, password_hash: str, password: str) -> bool:
        """Verifies if the plain text password matches the Argon2id hash."""
        try:
            return self._ph.verify(password_hash, password)
        except VerifyMismatchError:
            return False
        except Exception as e:
            logger.error("Error during password verification: %s", str(e))
            return False
