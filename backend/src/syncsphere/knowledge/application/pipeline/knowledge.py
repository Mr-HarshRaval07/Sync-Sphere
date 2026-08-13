import logging
import uuid
from typing import Optional, Dict, Any

from syncsphere.knowledge.domain.entities.source import KnowledgeSource
from syncsphere.knowledge.domain.entities.document import KnowledgeDocument
from syncsphere.knowledge.domain.entities.chunk import KnowledgeChunk
from syncsphere.knowledge.domain.repositories import (
    KnowledgeSourceRepository,
    KnowledgeDocumentRepository,
    KnowledgeChunkRepository
)
from syncsphere.knowledge.application.services.loader import DocumentLoader, DocumentParser, DocumentNormalizer
from syncsphere.knowledge.application.services.chunking import ChunkingEngine
from syncsphere.knowledge.application.services.embedding import EmbeddingPipeline, EmbeddingVersionManager
from syncsphere.knowledge.application.services.vector import VectorStore

logger = logging.getLogger("syncsphere.knowledge.application.pipeline.knowledge")

class KnowledgePipeline:
    """
    Decoupled orchestrator executing knowledge indexing lifecycle:
    Import -> Parse -> Normalize -> Chunk -> Embed -> Index -> Graph -> Statistics
    """
    
    def __init__(
        self,
        source_repo: KnowledgeSourceRepository,
        document_repo: KnowledgeDocumentRepository,
        chunk_repo: KnowledgeChunkRepository,
        vector_store: VectorStore,
        embedding_pipeline: EmbeddingPipeline
    ) -> None:
        self.source_repo = source_repo
        self.document_repo = document_repo
        self.chunk_repo = chunk_repo
        self.vector_store = vector_store
        self.embedding_pipeline = embedding_pipeline

    async def execute(self, org_id: str, source: KnowledgeSource, raw_content: Optional[str] = None) -> KnowledgeDocument:
        logger.info("Executing knowledge pipeline for source: '%s' (type: %s)", source.name, source.type.value)
        source.start_sync()
        await self.source_repo.save(source)
        
        try:
            # 1. Import Stage
            if not raw_content:
                raw_content = await DocumentLoader.load(source.config)
                
            # 2. Parse Stage
            parsed = DocumentParser.parse(raw_content, mime_type="text/plain")
            
            # 3. Normalize Stage
            normalized = DocumentNormalizer.normalize(parsed)
            
            # 4. Synthesize Document Entity & save
            doc_id = str(uuid.uuid4())
            document = KnowledgeDocument(
                source_id=source.id,
                org_id=org_id,
                title=source.name,
                content=normalized,
                id=doc_id
            )
            await self.document_repo.save(document)
            
            # 5. Chunk Stage
            policy = source.policy
            chunk_texts = ChunkingEngine.chunk(
                text=normalized,
                strategy=policy.chunking_strategy,
                chunk_size=policy.chunk_size,
                chunk_overlap=policy.chunk_overlap
            )
            
            # 6. Embed Stage
            vectors = await self.embedding_pipeline.generate(
                org_id=org_id,
                texts=chunk_texts,
                model_name=policy.embedding_model
            )
            
            # 7. Index Stage
            # Create EmbeddingVersion record
            dimensions = len(vectors[0]) if vectors else 1536
            version_record = EmbeddingVersionManager.create_version(policy.embedding_model, dimensions)
            
            # Delete old chunks for this source if they exist
            await self.vector_store.delete_by_source(source.id)
            
            for idx, (text, vector) in enumerate(zip(chunk_texts, vectors)):
                chunk = KnowledgeChunk(
                    document_id=doc_id,
                    source_id=source.id,
                    org_id=org_id,
                    text=text,
                    token_count=int(len(text) / 4),  # rough token estimation
                    embedding=vector,
                    embedding_version_id=version_record.version_id,
                    index_status="indexed",
                    id=str(uuid.uuid4())
                )
                # Save chunk to mongo & vector index
                await self.vector_store.upsert_chunk(chunk)
                
            # 8. Graph & Relationships Stage
            # Extract simple concept linkages (e.g. self-citations)
            document.add_relationship(doc_id, "REFERENCES", weight=1.0)
            await self.document_repo.save(document)
            
            # 9. Statistics & Completion
            source.complete_sync()
            await self.source_repo.save(source)
            
            logger.info("Knowledge pipeline completed successfully. Generated %d chunks.", len(chunk_texts))
            return document
            
        except Exception as e:
            logger.exception("Knowledge pipeline failed for source: %s", source.id)
            source.fail_sync()
            await self.source_repo.save(source)
            raise e
