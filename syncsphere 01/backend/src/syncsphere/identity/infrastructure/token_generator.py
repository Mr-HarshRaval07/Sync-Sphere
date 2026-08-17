import secrets
import hashlib
from typing import Tuple

class TokenGeneratorService:
    """Generates secure API Keys and Refresh Token strings and their SHA-256 hashes."""

    @staticmethod
    def generate_api_key() -> Tuple[str, str, str]:
        """
        Generates a live API Key.
        Returns:
            Tuple[raw_key, key_prefix, key_hash]
        """
        raw_token = secrets.token_hex(32)
        key_prefix = "sk_live_" + raw_token[:8]
        raw_key = f"sk_live_{raw_token}"
        key_hash = hashlib.sha256(raw_key.encode("utf-8")).hexdigest()
        return raw_key, key_prefix, key_hash

    @staticmethod
    def generate_refresh_token() -> Tuple[str, str]:
        """
        Generates a secure random refresh token.
        Returns:
            Tuple[raw_token, token_hash]
        """
        raw_token = secrets.token_urlsafe(64)
        token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
        return raw_token, token_hash

    @staticmethod
    def hash_token(raw_token: str) -> str:
        """Helper to generate a SHA-256 hash from a raw token string."""
        return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
