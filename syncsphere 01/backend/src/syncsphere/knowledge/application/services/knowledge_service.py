import logging
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional

from syncsphere.shared_kernel.types.result import Result
from syncsphere.shared_kernel.domain.domain_exception import EntityNotFoundException
from syncsphere.core.events.interfaces import EventPublisher
from syncsphere.knowledge.domain.entities.source import KnowledgeSource
from syncsphere.knowledge.domain.entities.document import KnowledgeDocument
from syncsphere.knowledge.domain.repositories import (
    KnowledgeSourceRepository,
    KnowledgeDocumentRepository,
    KnowledgeChunkRepository,
    SemanticCacheRepository
)
from syncsphere.knowledge.domain.value_objects import (
    KnowledgeStatistics,
    KnowledgeContext,
    KnowledgeGraphNode,
    KnowledgeGraphEdge,
    KnowledgeSearchResult,
    EmbeddingVersion,
    EmbeddingMigration
)
from syncsphere.knowledge.application.commands import (
    ImportKnowledgeCommand,
    DeleteKnowledgeCommand,
    UpdateKnowledgeCommand,
    GenerateEmbeddingsCommand,
    ReindexKnowledgeCommand,
    InvalidateCacheCommand,
    StoreConversationMemoryCommand,
    StoreWorkflowMemoryCommand,
    MigrateEmbeddingsCommand
)
from syncsphere.knowledge.application.queries import (
    SearchKnowledgeQuery,
    SearchConversationQuery,
    GetKnowledgeGraphQuery,
    GetKnowledgeStatisticsQuery
)
from syncsphere.knowledge.application.pipeline.knowledge import KnowledgePipeline
from syncsphere.knowledge.application.pipeline.retrieval import RetrievalPipeline
from syncsphere.knowledge.application.services.cache import SemanticCacheService, CacheInvalidator
from syncsphere.knowledge.application.services.graph import KnowledgeGraphBuilder
from syncsphere.knowledge.application.services.memory import MemoryService
from syncsphere.knowledge.application.services.sync import ConnectorSyncService
from syncsphere.knowledge.application.services.embedding import EmbeddingVersionManager
from syncsphere.knowledge.domain.events import (
    KnowledgeImported,
    KnowledgeIndexed,
    KnowledgeDeleted,
    KnowledgeUpdated,
    SearchExecuted,
    CacheHit,
    CacheMiss,
    ConversationStored,
    MemoryUpdated,
    KnowledgeGraphUpdated
)

logger = logging.getLogger("syncsphere.knowledge.application.services.knowledge_service")

class KnowledgeApplicationService:
    """
    Main orchestrating Application Service coordinating commands, queries, event bus publishing,
    knowledge pipelines, retrieval pipelines, semantic caching, and memories.
    """
    
    def __init__(
        self,
        source_repo: KnowledgeSourceRepository,
        document_repo: KnowledgeDocumentRepository,
        chunk_repo: KnowledgeChunkRepository,
        cache_repo: SemanticCacheRepository,
        knowledge_pipeline: KnowledgePipeline,
        retrieval_pipeline: RetrievalPipeline,
        cache_service: SemanticCacheService,
        memory_service: MemoryService,
        sync_service: ConnectorSyncService,
        event_bus: EventPublisher
    ) -> None:
        self.source_repo = source_repo
        self.document_repo = document_repo
        self.chunk_repo = chunk_repo
        self.cache_repo = cache_repo
        self.knowledge_pipeline = knowledge_pipeline
        self.retrieval_pipeline = retrieval_pipeline
        self.cache_service = cache_service
        self.memory_service = memory_service
        self.sync_service = sync_service
        self.event_bus = event_bus

    async def import_knowledge(self, cmd: ImportKnowledgeCommand) -> Result[KnowledgeSource, Exception]:
        """Creates a new knowledge source and triggers background indexing pipeline."""
        source_id = str(uuid.uuid4())
        source = KnowledgeSource(
            org_id=cmd.org_id,
            name=cmd.name,
            type=cmd.type,
            config=cmd.config,
            policy=cmd.policy,
            sync_strategy=cmd.sync_strategy,
            sync_schedule=cmd.sync_schedule,
            id=source_id
        )
        
        await self.source_repo.save(source)
        
        # Execute pipeline synchronously/asynchronously
        try:
            await self.knowledge_pipeline.execute(cmd.org_id, source)
            
            corr_id = cmd.correlation_id or str(uuid.uuid4())
            await self.event_bus.publish(KnowledgeImported(
                correlation_id=corr_id,
                org_id=cmd.org_id,
                source_id=source_id,
                documents_count=1
            ))
            return Result.ok(source)
        except Exception as e:
            return Result.fail(e)

    async def delete_knowledge(self, cmd: DeleteKnowledgeCommand) -> Result[bool, Exception]:
        """Purges a knowledge source and all of its compiled chunks."""
        source = await self.source_repo.get_by_id(cmd.source_id)
        if not source or source.org_id != cmd.org_id:
            return Result.fail(EntityNotFoundException("KNOWLEDGE_SOURCE_NOT_FOUND", "Source not found."))
            
        await self.source_repo.delete(cmd.source_id)
        await self.knowledge_pipeline.vector_store.delete_by_source(cmd.source_id)
        
        # Delete documents associated with this source
        docs = await self.document_repo.list_by_source(cmd.source_id)
        for doc in docs:
            await self.document_repo.delete(doc.id)
            await self.chunk_repo.delete_by_document(doc.id)
            
        corr_id = cmd.correlation_id or str(uuid.uuid4())
        await self.event_bus.publish(KnowledgeDeleted(
            correlation_id=corr_id,
            org_id=cmd.org_id,
            source_id=cmd.source_id
        ))
        return Result.ok(True)

    async def update_knowledge(self, cmd: UpdateKnowledgeCommand) -> Result[KnowledgeDocument, Exception]:
        """Edits an existing document text and triggers re-indexing for that document."""
        doc = await self.document_repo.get_by_id(cmd.doc_id)
        if not doc or doc.org_id != cmd.org_id:
            return Result.fail(EntityNotFoundException("KNOWLEDGE_DOCUMENT_NOT_FOUND", "Document not found."))
            
        doc.title = cmd.title
        doc.content = cmd.content
        doc.version += 1
        await self.document_repo.save(doc)
        
        # Re-run chunking/embedding pipeline for this document text
        source = await self.source_repo.get_by_id(doc.source_id)
        if source:
            await self.knowledge_pipeline.execute(cmd.org_id, source, raw_content=cmd.content)
            
        corr_id = cmd.correlation_id or str(uuid.uuid4())
        await self.event_bus.publish(KnowledgeUpdated(
            correlation_id=corr_id,
            org_id=cmd.org_id,
            document_id=cmd.doc_id,
            version=doc.version
        ))
        return Result.ok(doc)

    async def reindex_knowledge(self, cmd: ReindexKnowledgeCommand) -> Result[bool, Exception]:
        """Forces total re-indexing for a target knowledge source."""
        source = await self.source_repo.get_by_id(cmd.source_id)
        if not source or source.org_id != cmd.org_id:
            return Result.fail(EntityNotFoundException("KNOWLEDGE_SOURCE_NOT_FOUND", "Source not found."))
            
        try:
            await self.knowledge_pipeline.execute(cmd.org_id, source)
            corr_id = cmd.correlation_id or str(uuid.uuid4())
            await self.event_bus.publish(KnowledgeIndexed(
                correlation_id=corr_id,
                org_id=cmd.org_id,
                source_id=cmd.source_id,
                chunks_count=0  # dynamic update
            ))
            return Result.ok(True)
        except Exception as e:
            return Result.fail(e)

    async def invalidate_cache(self, cmd: InvalidateCacheCommand) -> Result[bool, Exception]:
        """Clears/invalidates semantic cache keys."""
        try:
            await CacheInvalidator.invalidate(self.cache_repo, cmd.org_id, cmd.query_text)
            return Result.ok(True)
        except Exception as e:
            return Result.fail(e)

    # Search Queries
    async def search_knowledge(self, query: SearchKnowledgeQuery) -> Result[KnowledgeContext, Exception]:
        """Looks up context semantically (utilizing cache first, then hybrid pipeline)."""
        # 1. Lookup in semantic cache
        cached_text = await self.cache_service.lookup(query.org_id, query.query, namespace=query.namespace or "default")
        if cached_text:
            corr_id = query.correlation_id or str(uuid.uuid4())
            await self.event_bus.publish(CacheHit(
                correlation_id=corr_id,
                org_id=query.org_id,
                query=query.query,
                entry_id="cached_entry"
            ))
            return Result.ok(KnowledgeContext(context_str=cached_text))
            
        # 2. Cache Miss: Run hybrid retrieval pipeline
        try:
            context = await self.retrieval_pipeline.execute(query)
            
            # Store in semantic cache for future hits
            await self.cache_service.store(
                org_id=query.org_id,
                query=query.query,
                response=context.context_str,
                namespace=query.namespace or "default"
            )
            
            corr_id = query.correlation_id or str(uuid.uuid4())
            await self.event_bus.publish(CacheMiss(
                correlation_id=corr_id,
                org_id=query.org_id,
                query=query.query
            ))
            await self.event_bus.publish(SearchExecuted(
                correlation_id=corr_id,
                org_id=query.org_id,
                query=query.query,
                policy=query.policy.value,
                results_count=len(context.citations)
            ))
            return Result.ok(context)
        except Exception as e:
            return Result.fail(e)

    # Graph Retrieval
    async def get_knowledge_graph(self, query: GetKnowledgeGraphQuery) -> Result[Dict[str, Any], Exception]:
        """Assembles and traversals document concept maps."""
        docs = await self.document_repo.list_by_org(query.org_id)
        if query.namespace:
            docs = [d for d in docs if d.namespace == query.namespace]
            
        graph = KnowledgeGraphBuilder.build(docs)
        corr_id = query.correlation_id or str(uuid.uuid4())
        await self.event_bus.publish(KnowledgeGraphUpdated(
            correlation_id=corr_id,
            org_id=query.org_id,
            node_id="graph_compiled"
        ))
        return Result.ok(graph)

    # Statistics Query
    async def get_statistics(self, query: GetKnowledgeStatisticsQuery) -> Result[KnowledgeStatistics, Exception]:
        """Calculates global storage indices counts."""
        sources = await self.source_repo.list_by_org(query.org_id)
        docs = await self.document_repo.list_by_org(query.org_id)
        chunks = await self.chunk_repo.list_by_org(query.org_id)
        
        stats = KnowledgeStatistics(
            total_sources=len(sources),
            total_documents=len(docs),
            total_chunks=len(chunks),
            index_size_bytes=sum(len(c.text) for c in chunks) * 4
        )
        return Result.ok(stats)

    # Memory Store and Query Operations
    async def store_conversation_memory(self, cmd: StoreConversationMemoryCommand) -> Result[bool, Exception]:
        payload = {
            "session_id": cmd.session_id,
            "messages": cmd.messages,
            "summary": cmd.summary,
            "updated_at": datetime.utcnow().isoformat()
        }
        await self.memory_service.save_conversation_memory(cmd.org_id, cmd.session_id, payload)
        corr_id = cmd.correlation_id or str(uuid.uuid4())
        await self.event_bus.publish(ConversationStored(
            correlation_id=corr_id,
            org_id=cmd.org_id,
            session_id=cmd.session_id
        ))
        return Result.ok(True)

    async def store_workflow_memory(self, cmd: StoreWorkflowMemoryCommand) -> Result[bool, Exception]:
        payload = {
            "workflow_id": cmd.workflow_id,
            "context_keys": cmd.context_keys,
            "statistics": cmd.statistics or {},
            "updated_at": datetime.utcnow().isoformat()
        }
        await self.memory_service.save_workflow_memory(cmd.org_id, cmd.workflow_id, payload)
        corr_id = cmd.correlation_id or str(uuid.uuid4())
        await self.event_bus.publish(MemoryUpdated(
            correlation_id=corr_id,
            org_id=cmd.org_id,
            memory_type="workflow",
            resource_id=cmd.workflow_id
        ))
        return Result.ok(True)

    async def migrate_source_embeddings_safely(self, cmd: MigrateEmbeddingsCommand) -> Result[EmbeddingMigration, Exception]:
        """
        Executes a zero-downtime embedding model migration for all documents under a source.
        1. Validates the source.
        2. Creates an EmbeddingMigration tracker.
        3. Generates new embeddings with temporary state.
        4. Replaces old chunks atomically once all new chunks are ready.
        """
        source = await self.source_repo.get_by_id(cmd.source_id)
        if not source or source.org_id != cmd.org_id:
            return Result.fail(EntityNotFoundException("KNOWLEDGE_SOURCE_NOT_FOUND", "Source not found."))
            
        current_model = source.policy.embedding_model
        if current_model == cmd.target_model_name:
            # Already matches, compile dummy completed migration
            dummy = EmbeddingMigration(
                migration_id=str(uuid.uuid4()),
                source_version_id=current_model,
                target_version_id=cmd.target_model_name,
                reindex_completed=True,
                status="completed",
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow()
            )
            return Result.ok(dummy)

        # Create migration record
        migration = EmbeddingMigration(
            migration_id=str(uuid.uuid4()),
            source_version_id=current_model,
            target_version_id=cmd.target_model_name,
            reindex_completed=False,
            status="running",
            started_at=datetime.utcnow()
        )

        new_chunks = []
        try:
            # Fetch all documents of this source
            docs = await self.document_repo.list_by_source(source.id)
            
            # Generate new target version fingerprint
            target_version_record = EmbeddingVersionManager.create_version(cmd.target_model_name, 1536) # default 1536 dims
            
            for doc in docs:
                # Chunk document content using the chunking engine configuration from the policy
                from syncsphere.knowledge.application.services.chunking import ChunkingEngine
                from syncsphere.knowledge.domain.entities.chunk import KnowledgeChunk
                
                chunk_texts = ChunkingEngine.chunk(
                    text=doc.content,
                    strategy=source.policy.chunking_strategy,
                    chunk_size=source.policy.chunk_size,
                    chunk_overlap=source.policy.chunk_overlap
                )
                
                # Embed the text chunks using target model
                vectors = await self.knowledge_pipeline.embedding_pipeline.generate(
                    org_id=cmd.org_id,
                    texts=chunk_texts,
                    model_name=cmd.target_model_name
                )
                
                # Create chunks with temporary state "migrating" so they aren't retrieved during current searches
                for idx, (text, vector) in enumerate(zip(chunk_texts, vectors)):
                    chunk = KnowledgeChunk(
                        document_id=doc.id,
                        source_id=source.id,
                        org_id=cmd.org_id,
                        text=text,
                        token_count=int(len(text) / 4),
                        embedding=vector,
                        embedding_version_id=target_version_record.version_id,
                        index_status="migrating",
                        id=str(uuid.uuid4())
                    )
                    await self.chunk_repo.save(chunk)
                    new_chunks.append(chunk)

            # Atomically update status of temporary new chunks to "indexed" and delete old chunks
            for chunk in new_chunks:
                chunk.index_status = "indexed"
                await self.chunk_repo.save(chunk)
                await self.knowledge_pipeline.vector_store.upsert_chunk(chunk)

            # Delete old chunks for this source (all chunks with the old version)
            all_source_chunks = await self.chunk_repo.list_by_org(cmd.org_id)
            for old_c in all_source_chunks:
                if old_c.source_id == source.id and old_c.embedding_version_id != target_version_record.version_id:
                    await self.chunk_repo.delete(old_c.id)
                    
            # Update source policy and status
            source.policy.embedding_model = cmd.target_model_name
            await self.source_repo.save(source)
            
            migration.status = "completed"
            migration.reindex_completed = True
            migration.completed_at = datetime.utcnow()
            
            # Publish event
            from syncsphere.knowledge.domain.events import KnowledgeIndexed
            corr_id = cmd.correlation_id or str(uuid.uuid4())
            await self.event_bus.publish(KnowledgeIndexed(
                correlation_id=corr_id,
                org_id=cmd.org_id,
                source_id=source.id,
                chunks_count=len(new_chunks)
            ))
            
            return Result.ok(migration)

        except Exception as e:
            logger.exception("Safe embedding migration failed for source %s", source.id)
            # Rollback: Clean up new temporary migrating chunks
            for chunk in new_chunks:
                await self.chunk_repo.delete(chunk.id)
                
            migration.status = "failed"
            migration.completed_at = datetime.utcnow()
            return Result.fail(e)
