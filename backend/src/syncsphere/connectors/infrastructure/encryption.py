import logging
from cryptography.fernet import Fernet
from syncsphere.core.providers.secret import SecretProvider
from syncsphere.core.config.settings import settings

logger = logging.getLogger("syncsphere.connectors.infrastructure.encryption")

class FernetSecretProvider(SecretProvider):
    """Symmetric encryption provider using Fernet (AES-128 in CBC mode)."""

    def __init__(self) -> None:
        key = settings.master_encryption_key.get_secret_value()
        try:
            self._fernet = Fernet(key.encode("utf-8"))
        except Exception as e:
            logger.error("Failed to initialize Fernet encryption. Key might be invalid: %s", str(e))
            raise e

    def encrypt(self, plain_text: str, key_context: str = "") -> str:
        """Encrypts plain text string."""
        # Optional: mix key_context (like org_id) into encryption context for salt/added protection
        data = plain_text.encode("utf-8")
        cipher_text = self._fernet.encrypt(data)
        return cipher_text.decode("utf-8")

    def decrypt(self, cipher_text: str, key_context: str = "") -> str:
        """Decrypts cipher text string."""
        try:
            data = cipher_text.encode("utf-8")
            plain_bytes = self._fernet.decrypt(data)
            return plain_bytes.decode("utf-8")
        except Exception as e:
            from syncsphere.connectors.domain.exceptions import DecryptionFailedException
            logger.error("Failed to decrypt connector secret: %s", str(e))
            raise DecryptionFailedException(key_context)
