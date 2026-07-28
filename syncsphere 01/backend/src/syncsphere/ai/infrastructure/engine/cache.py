import time
import hashlib
import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("syncsphere.ai.infrastructure.engine.cache")

class InferenceCache:
    """
    In-memory cache supporting response reuse with TTL (Time To Live)
    expirations based on cryptographic request hashes.
    """
    def __init__(self, default_ttl_seconds: float = 300.0) -> None:
        self.default_ttl_seconds = default_ttl_seconds
        # key -> (value, expire_at)
        self._store: Dict[str, tuple] = {}

    def _compute_key(self, prompt_or_messages: Any, settings: Any) -> str:
        """Computes SHA-256 fingerprint hash of input payload and inference parameters."""
        serialized_input = json.dumps(prompt_or_messages, sort_keys=True)
        serialized_settings = ""
        if settings:
            # Check if settings has model_dump (Pydantic)
            if hasattr(settings, "model_dump"):
                serialized_settings = json.dumps(settings.model_dump(), sort_keys=True)
            elif hasattr(settings, "__dict__"):
                serialized_settings = json.dumps(settings.__dict__, sort_keys=True)
            else:
                serialized_settings = str(settings)
                
        hasher = hashlib.sha256()
        hasher.update(serialized_input.encode("utf-8"))
        hasher.update(serialized_settings.encode("utf-8"))
        return hasher.hexdigest()

    def get(self, prompt_or_messages: Any, settings: Any) -> Optional[Any]:
        """Retrieves cached response if present and not expired."""
        key = self._compute_key(prompt_or_messages, settings)
        record = self._store.get(key)
        if not record:
            return None
            
        value, expire_at = record
        if time.time() > expire_at:
            # Evict expired entry
            del self._store[key]
            return None
            
        logger.info("Inference cache hit for key: %s", key)
        return value

    def set(self, prompt_or_messages: Any, settings: Any, value: Any, ttl: Optional[float] = None) -> None:
        """Stores a resolved response with a specified TTL."""
        key = self._compute_key(prompt_or_messages, settings)
        ttl = ttl if ttl is not None else self.default_ttl_seconds
        expire_at = time.time() + ttl
        self._store[key] = (value, expire_at)
