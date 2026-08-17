import logging
from typing import List, Dict, Optional, Any
from datetime import datetime
import hashlib

from syncsphere.ai.domain.services.ai_gateway import AIGateway
from syncsphere.knowledge.domain.value_objects import EmbeddingVersion

logger = logging.getLogger("syncsphere.knowledge.application.services.embedding")

class EmbeddingCache:
    """In-memory cache for mapping text blocks to generated float vectors to prevent redundant gateway roundtrips."""
    
    def __init__(self) -> None:
        self._cache: Dict[str, List[float]] = {}

    def _hash_key(self, text: str, model_name: str) -> str:
        h = hashlib.sha256()
        h.update(f"{model_name}:{text}".encode("utf-8"))
        return h.hexdigest()

    def get(self, text: str, model_name: str) -> Optional[List[float]]:
        key = self._hash_key(text, model_name)
        return self._cache.get(key)

    def set(self, text: str, model_name: str, embedding: List[float]) -> None:
        key = self._hash_key(text, model_name)
        self._cache[key] = embedding

    def clear(self) -> None:
        self._cache.clear()


class EmbeddingBatcher:
    """Batches list of raw strings to invoke AI Gateway in chunks to optimize concurrency."""
    
    @staticmethod
    def batch(texts: List[str], batch_size: int = 16) -> List[List[str]]:
        batches = []
        for i in range(0, len(texts), batch_size):
            batches.append(texts[i:i + batch_size])
        return batches


class EmbeddingVersionManager:
    """Manages index versioning configurations and schema/model migrations."""
    
    @staticmethod
    def create_version(model_name: str, dimensions: int) -> EmbeddingVersion:
        fingerprint = hashlib.md5(f"{model_name}:{dimensions}".encode("utf-8")).hexdigest()
        return EmbeddingVersion(
            version_id=f"v_{model_name.replace('/', '_')}",
            model_name=model_name,
            dimensions=dimensions,
            created_at=datetime.utcnow(),
            compatibility_fingerprint=fingerprint
        )

    @staticmethod
    def validate_compatibility(v1: EmbeddingVersion, v2: EmbeddingVersion) -> bool:
        """Embedding models are compatible only if their compatibility fingerprints match."""
        return v1.compatibility_fingerprint == v2.compatibility_fingerprint


class EmbeddingPipeline:
    """Orchestrates generating embeddings for chunks via the AI Gateway, employing caches and batching."""
    
    def __init__(self, ai_gateway: AIGateway, cache: Optional[EmbeddingCache] = None) -> None:
        self.ai_gateway = ai_gateway
        self.cache = cache or EmbeddingCache()

    async def generate(self, org_id: str, texts: List[str], model_name: str = "text-embedding-004") -> List[List[float]]:
        """Generates embedding vectors, pulling from cache first, then batching gateway requests."""
        results = [None] * len(texts)
        missing_indices = []
        missing_texts = []
        
        # 1. Check cache
        for idx, text in enumerate(texts):
            cached = self.cache.get(text, model_name)
            if cached is not None:
                results[idx] = cached
            else:
                missing_indices.append(idx)
                missing_texts.append(text)
                
        # 2. Batch and request missing texts
        if missing_texts:
            batches = EmbeddingBatcher.batch(missing_texts, batch_size=8)
            all_vectors = []
            
            for batch in batches:
                # Gateway signature: generate_embedding(self, org_id: str, input_texts: List[str], correlation_id: Optional[str] = None) -> List[List[float]]
                vectors = await self.ai_gateway.generate_embedding(
                    org_id=org_id,
                    input_texts=batch,
                    correlation_id="knowledge-embedding-pipeline"
                )
                all_vectors.extend(vectors)
                
            # 3. Populate cache and outputs
            for idx, text, vector in zip(missing_indices, missing_texts, all_vectors):
                self.cache.set(text, model_name, vector)
                results[idx] = vector
                
        return results
