import logging
from datetime import datetime
from typing import Optional, List
import uuid

from syncsphere.knowledge.domain.entities.cache_entry import SemanticCacheEntry
from syncsphere.knowledge.domain.repositories import SemanticCacheRepository
from syncsphere.knowledge.application.services.vector import cosine_similarity
from syncsphere.knowledge.application.services.embedding import EmbeddingPipeline

logger = logging.getLogger("syncsphere.knowledge.application.services.cache")

class SimilarityThreshold:
    """Computes similarity metrics and checks if they pass configurable match bounds."""
    @staticmethod
    def is_match(v1: List[float], v2: List[float], threshold: float = 0.85) -> bool:
        score = cosine_similarity(v1, v2)
        return score >= threshold


class CacheMatcher:
    """Compares incoming queries to existing cache entries by calculating vector distance."""
    @staticmethod
    def match(
        query_vector: List[float],
        entries: List[SemanticCacheEntry]
    ) -> Optional[SemanticCacheEntry]:
        best_entry = None
        best_score = -1.0
        
        for entry in entries:
            score = cosine_similarity(query_vector, entry.embedding)
            if score >= entry.similarity_threshold and score > best_score:
                best_score = score
                best_entry = entry
                
        return best_entry


class CacheInvalidator:
    """Manages cache eviction policies, TTLs, and explicit cache clears."""
    @staticmethod
    async def invalidate(repo: SemanticCacheRepository, org_id: str, query_text: Optional[str] = None) -> None:
        if query_text:
            logger.info("Invalidating specific semantic cache query for tenant: %s", org_id)
            # Find and delete matching query entries
            entries = await repo.list_by_org(org_id)
            for entry in entries:
                if entry.query_text.strip().lower() == query_text.strip().lower():
                    await repo.delete(entry.id)
        else:
            logger.info("Purging entire semantic cache for tenant: %s", org_id)
            await repo.clear_by_org(org_id)


class SemanticCacheService:
    """Semantic Cache coordinator providing vector-comparable query-response memoization."""
    
    def __init__(
        self,
        repo: SemanticCacheRepository,
        embedding_pipeline: EmbeddingPipeline
    ) -> None:
        self.repo = repo
        self.embedding_pipeline = embedding_pipeline

    async def lookup(
        self,
        org_id: str,
        query: str,
        threshold: float = 0.85,
        namespace: str = "default"
    ) -> Optional[str]:
        """Looks up a query semantically in the cache repository."""
        # Generate query vector
        vectors = await self.embedding_pipeline.generate(org_id, [query])
        if not vectors:
            return None
        query_vector = vectors[0]
        
        entries = await self.repo.list_by_org(org_id)
        # Filter by namespace
        entries = [e for e in entries if e.namespace == namespace]
        
        match = CacheMatcher.match(query_vector, entries)
        if match:
            logger.info("Semantic cache HIT for query: '%s' (matched: '%s')", query, match.query_text)
            match.record_hit()
            await self.repo.save(match)
            return match.response_text
            
        logger.info("Semantic cache MISS for query: '%s'", query)
        return None

    async def store(
        self,
        org_id: str,
        query: str,
        response: str,
        threshold: float = 0.85,
        namespace: str = "default",
        policy: str = "LRU"
    ) -> None:
        """Stores a query-response pair in the semantic cache."""
        vectors = await self.embedding_pipeline.generate(org_id, [query])
        if not vectors:
            return
        query_vector = vectors[0]
        
        entry = SemanticCacheEntry(
            org_id=org_id,
            query_text=query,
            response_text=response,
            embedding=query_vector,
            similarity_threshold=threshold,
            namespace=namespace,
            eviction_policy=policy,
            id=str(uuid.uuid4())
        )
        await self.repo.save(entry)
        logger.info("Stored query-response in semantic cache: '%s'", query)
