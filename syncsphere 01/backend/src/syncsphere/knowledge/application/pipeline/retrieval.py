import logging
import uuid
from typing import List, Dict, Any, Optional

from syncsphere.knowledge.application.queries import SearchKnowledgeQuery
from syncsphere.knowledge.domain.value_objects import (
    RetrievalPolicy,
    KnowledgeContext,
    KnowledgeCitation,
    KnowledgeReference,
    KnowledgeSearchResult,
)
from syncsphere.knowledge.application.services.vector import VectorStore
from syncsphere.knowledge.application.services.embedding import EmbeddingPipeline
from syncsphere.knowledge.domain.repositories import KnowledgeDocumentRepository

logger = logging.getLogger("syncsphere.knowledge.application.pipeline.retrieval")

class RetrievalPipeline:
    """
    Decoupled internal orchestrator executing search queries through RAG pipeline stages:
    Query -> Query Expansion -> Retrieval -> Re-ranking -> Context Building -> Citation Building.
    """
    
    def __init__(
        self,
        vector_store: VectorStore,
        embedding_pipeline: EmbeddingPipeline,
        document_repo: KnowledgeDocumentRepository
    ) -> None:
        self.vector_store = vector_store
        self.embedding_pipeline = embedding_pipeline
        self.document_repo = document_repo

    async def execute(self, query: SearchKnowledgeQuery) -> KnowledgeContext:
        logger.info("Executing retrieval pipeline for query: '%s' with policy: %s", query.query, query.policy.value)
        
        # 1. Query Expansion Stage
        expanded_queries = await self._expand_query(query.query, query.policy)
        
        # 2. Retrieval Stage
        # Resolve parameters based on RetrievalPolicy
        top_k = query.top_k
        if query.policy == RetrievalPolicy.FAST:
            top_k = min(top_k, 3)
        elif query.policy == RetrievalPolicy.ACCURATE:
            top_k = max(top_k, 8)
            
        retrieved_chunks = []
        if query.policy != RetrievalPolicy.CHEAP:
            # Generate embedding vector for expanded queries
            for eq in expanded_queries:
                vectors = await self.embedding_pipeline.generate(query.org_id, [eq])
                if vectors:
                    chunks = await self.vector_store.similarity_search(
                        org_id=query.org_id,
                        query_vector=vectors[0],
                        top_k=top_k,
                        namespace=query.namespace
                    )
                    retrieved_chunks.extend(chunks)
        else:
            # Cheap policy performs purely database-level text scan
            # We can mock this by loading all chunks and filtering matching words
            all_chunks = await self.vector_store.chunk_repo.list_by_org(query.org_id)
            if query.namespace:
                all_chunks = [c for c in all_chunks if c.namespace == query.namespace]
            # Simple keyword search
            words = query.query.lower().split()
            matched = []
            for chunk in all_chunks:
                score = sum(1 for w in words if w in chunk.text.lower())
                if score > 0:
                    matched.append((chunk, score))
            matched.sort(key=lambda x: x[1], reverse=True)
            retrieved_chunks = [m[0] for m in matched[:top_k]]

        # Dedup chunks by ID
        seen = set()
        deduped_chunks = []
        for c in retrieved_chunks:
            if c.id not in seen:
                seen.add(c.id)
                deduped_chunks.append(c)
                
        # 3. Re-ranking Stage
        ranked_results = await self._rerank(query.query, deduped_chunks)
        
        # 4. Citation Building Stage
        citations = []
        for idx, chunk in enumerate(ranked_results):
            # Fetch document information
            doc = await self.document_repo.get_by_id(chunk.document_id)
            doc_title = doc.title if doc else "Source Document"
            doc_source = doc.source_id if doc else "unknown"
            
            ref = KnowledgeReference(
                document_id=chunk.document_id,
                source_id=doc_source,
                title=doc_title,
                location=f"Chunk {idx + 1}"
            )
            citation = KnowledgeCitation(
                citation_id=f"CIT-{idx + 1}",
                text_snippet=chunk.text[:200] + "...",
                reference=ref
            )
            citations.append(citation)
            
        # 5. Context Building Stage
        context_parts = []
        for citation, chunk in zip(citations, ranked_results):
            context_parts.append(f"[{citation.citation_id}] ({citation.reference.title}):\n{chunk.text}\n")
            
        context_str = "\n".join(context_parts)
        
        return KnowledgeContext(
            context_str=context_str,
            citations=citations
        )

    async def _expand_query(self, query: str, policy: RetrievalPolicy) -> List[str]:
        """Expands query synonyms or variations based on policy."""
        expanded = [query]
        if policy == RetrievalPolicy.ACCURATE:
            # Accurate retrieval runs multi-query expansion
            # Add simple synonym/keyword splits for higher recall
            words = query.split()
            if len(words) > 1:
                expanded.append(" ".join(reversed(words)))
                expanded.extend(words[:3])
        return expanded

    async def _rerank(self, query: str, chunks: List[Any]) -> List[Any]:
        """Re-ranks retrieved chunks based on keyword matching frequency (BM25 fallback)."""
        scored = []
        query_words = query.lower().split()
        for chunk in chunks:
            text = chunk.text.lower()
            keyword_score = sum(text.count(w) for w in query_words)
            scored.append((chunk, keyword_score))
            
        # Sort descending by keyword density
        scored.sort(key=lambda x: x[1], reverse=True)
        return [s[0] for s in scored]
