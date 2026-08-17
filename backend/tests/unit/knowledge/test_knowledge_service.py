import pytest
import asyncio
from typing import List, Optional
import uuid

from syncsphere.shared_kernel.types.result import Result
from syncsphere.knowledge.domain.entities import KnowledgeSource, KnowledgeDocument
from syncsphere.knowledge.domain.value_objects import KnowledgeSourceType, RetrievalPolicy, ChunkingStrategy
from syncsphere.knowledge.application.commands import (
    ImportKnowledgeCommand,
    DeleteKnowledgeCommand,
    UpdateKnowledgeCommand,
    StoreConversationMemoryCommand,
    MigrateEmbeddingsCommand
)
from syncsphere.knowledge.application.queries import (
    SearchKnowledgeQuery,
    GetKnowledgeGraphQuery
)
from syncsphere.knowledge.application.pipeline.knowledge import KnowledgePipeline
from syncsphere.knowledge.application.pipeline.retrieval import RetrievalPipeline
from syncsphere.knowledge.application.services.embedding import EmbeddingPipeline, EmbeddingCache
from syncsphere.knowledge.application.services.vector import MongoDBVectorStore
from syncsphere.knowledge.application.services.cache import SemanticCacheService
from syncsphere.knowledge.application.services.memory import MemoryService
from syncsphere.knowledge.application.services.sync import ConnectorSyncService
from syncsphere.knowledge.application.services.knowledge_service import KnowledgeApplicationService
from tests.mocks import (
    InMemoryKnowledgeSourceRepository,
    InMemoryKnowledgeDocumentRepository,
    InMemoryKnowledgeChunkRepository,
    InMemorySemanticCacheRepository,
    InMemoryMemoryRepository
)

class MockEventPublisher:
    def __init__(self) -> None:
        self.published = []
    async def publish(self, event) -> None:
        self.published.append(event)

class MockAIGateway:
    async def generate_embedding(self, org_id: str, input_texts: List[str], correlation_id: Optional[str] = None) -> List[List[float]]:
        # Mock embedding return with dimensions = 3
        return [[0.8, 0.1, 0.1] for _ in input_texts]

class MockConnectorService:
    async def execute_tool(self, org_id: str, connector_id: str, tool_name: str, arguments: dict):
        class DummyContent:
            def __init__(self):
                self.content = [{"type": "text", "text": "Connector fetched data."}]
        return Result.ok(DummyContent())


@pytest.mark.asyncio
async def test_knowledge_pipeline_execution():
    source_repo = InMemoryKnowledgeSourceRepository()
    doc_repo = InMemoryKnowledgeDocumentRepository()
    chunk_repo = InMemoryKnowledgeChunkRepository()
    
    mock_ai = MockAIGateway()
    embed_pipeline = EmbeddingPipeline(ai_gateway=mock_ai, cache=EmbeddingCache())
    vector_store = MongoDBVectorStore(chunk_repo=chunk_repo)
    
    pipeline = KnowledgePipeline(
        source_repo=source_repo,
        document_repo=doc_repo,
        chunk_repo=chunk_repo,
        vector_store=vector_store,
        embedding_pipeline=embed_pipeline
    )
    
    source = KnowledgeSource(
        org_id="org_123",
        name="Test Source A",
        type=KnowledgeSourceType.TEXT,
        config={"text": "Hello world from the indexing pipeline. Clean architecture is modular."}
    )
    
    doc = await pipeline.execute("org_123", source)
    assert doc.id is not None
    assert doc.title == "Test Source A"
    assert doc.content == "Hello world from the indexing pipeline. Clean architecture is modular."
    
    chunks = await chunk_repo.list_by_document(doc.id)
    assert len(chunks) > 0
    assert chunks[0].embedding == [0.8, 0.1, 0.1]


@pytest.mark.asyncio
async def test_knowledge_service_commands_and_queries():
    source_repo = InMemoryKnowledgeSourceRepository()
    doc_repo = InMemoryKnowledgeDocumentRepository()
    chunk_repo = InMemoryKnowledgeChunkRepository()
    cache_repo = InMemorySemanticCacheRepository()
    memory_repo = InMemoryMemoryRepository()
    
    mock_ai = MockAIGateway()
    embed_pipeline = EmbeddingPipeline(ai_gateway=mock_ai, cache=EmbeddingCache())
    vector_store = MongoDBVectorStore(chunk_repo=chunk_repo)
    
    pipeline = KnowledgePipeline(
        source_repo=source_repo,
        document_repo=doc_repo,
        chunk_repo=chunk_repo,
        vector_store=vector_store,
        embedding_pipeline=embed_pipeline
    )
    
    retrieval_pipeline = RetrievalPipeline(
        vector_store=vector_store,
        embedding_pipeline=embed_pipeline,
        document_repo=doc_repo
    )
    
    cache_service = SemanticCacheService(repo=cache_repo, embedding_pipeline=embed_pipeline)
    memory_service = MemoryService(repo=memory_repo)
    
    sync_service = ConnectorSyncService(
        source_repo=source_repo,
        connector_service=MockConnectorService(),
        knowledge_pipeline=pipeline
    )
    
    bus = MockEventPublisher()
    
    svc = KnowledgeApplicationService(
        source_repo=source_repo,
        document_repo=doc_repo,
        chunk_repo=chunk_repo,
        cache_repo=cache_repo,
        knowledge_pipeline=pipeline,
        retrieval_pipeline=retrieval_pipeline,
        cache_service=cache_service,
        memory_service=memory_service,
        sync_service=sync_service,
        event_bus=bus
    )
    
    # 1. Test Import Source
    cmd_import = ImportKnowledgeCommand(
        org_id="org_abc",
        name="Source A",
        type=KnowledgeSourceType.TEXT,
        config={"text": "Orchestrating agent tasks is a planner role."},
        sync_strategy="incremental"
    )
    res_import = await svc.import_knowledge(cmd_import)
    assert res_import.is_ok
    source = res_import.value()
    assert source.id is not None
    assert len(bus.published) > 0
    assert bus.published[0].event_type == "knowledge.imported"
    
    # 2. Test Search Knowledge (Hybrid RAG query)
    query = SearchKnowledgeQuery(
        org_id="org_abc",
        query="planner tasks",
        policy=RetrievalPolicy.BALANCED,
        top_k=2
    )
    res_search = await svc.search_knowledge(query)
    assert res_search.is_ok
    context = res_search.value()
    assert "Orchestrating agent tasks is a planner role." in context.context_str
    
    # 3. Test Semantic Cache HIT on second search
    res_search_cache = await svc.search_knowledge(query)
    assert res_search_cache.is_ok
    # Assert cache hit event was raised
    event_types = [e.event_type for e in bus.published]
    assert "knowledge.cache_hit" in event_types
    
    # 4. Test Conversation Memory Stores
    cmd_mem = StoreConversationMemoryCommand(
        org_id="org_abc",
        session_id="session_123",
        messages=[{"role": "user", "content": "How's planning?"}],
        summary="planning discussions"
    )
    res_mem = await svc.store_conversation_memory(cmd_mem)
    assert res_mem.is_ok
    
    mem_data = await memory_service.get_conversation_memory("org_abc", "session_123")
    assert mem_data is not None
    assert mem_data["summary"] == "planning discussions"


@pytest.mark.asyncio
async def test_knowledge_embedding_migration():
    source_repo = InMemoryKnowledgeSourceRepository()
    doc_repo = InMemoryKnowledgeDocumentRepository()
    chunk_repo = InMemoryKnowledgeChunkRepository()
    cache_repo = InMemorySemanticCacheRepository()
    memory_repo = InMemoryMemoryRepository()
    
    mock_ai = MockAIGateway()
    embed_pipeline = EmbeddingPipeline(ai_gateway=mock_ai, cache=EmbeddingCache())
    vector_store = MongoDBVectorStore(chunk_repo=chunk_repo)
    
    pipeline = KnowledgePipeline(
        source_repo=source_repo,
        document_repo=doc_repo,
        chunk_repo=chunk_repo,
        vector_store=vector_store,
        embedding_pipeline=embed_pipeline
    )
    
    retrieval_pipeline = RetrievalPipeline(
        vector_store=vector_store,
        embedding_pipeline=embed_pipeline,
        document_repo=doc_repo
    )
    
    cache_service = SemanticCacheService(repo=cache_repo, embedding_pipeline=embed_pipeline)
    memory_service = MemoryService(repo=memory_repo)
    sync_service = ConnectorSyncService(
        source_repo=source_repo,
        connector_service=MockConnectorService(),
        knowledge_pipeline=pipeline
    )
    bus = MockEventPublisher()
    
    svc = KnowledgeApplicationService(
        source_repo=source_repo,
        document_repo=doc_repo,
        chunk_repo=chunk_repo,
        cache_repo=cache_repo,
        knowledge_pipeline=pipeline,
        retrieval_pipeline=retrieval_pipeline,
        cache_service=cache_service,
        memory_service=memory_service,
        sync_service=sync_service,
        event_bus=bus
    )
    
    # 1. Import source
    cmd_import = ImportKnowledgeCommand(
        org_id="org_abc",
        name="Migration Source",
        type=KnowledgeSourceType.TEXT,
        config={"text": "Old embedding model texts."},
        sync_strategy="incremental"
    )
    res_import = await svc.import_knowledge(cmd_import)
    source = res_import.value()
    
    # 2. Check initial model
    assert source.policy.embedding_model == "text-embedding-004"
    
    # Check that chunks exist under old version
    chunks_before = await chunk_repo.list_by_org("org_abc")
    assert len(chunks_before) > 0
    old_version_id = chunks_before[0].embedding_version_id
    assert old_version_id == "v_text-embedding-004"
    
    # 3. Trigger safe migration to new model
    cmd_migrate = MigrateEmbeddingsCommand(
        org_id="org_abc",
        source_id=source.id,
        target_model_name="text-embedding-3-small"
    )
    res_migrate = await svc.migrate_source_embeddings_safely(cmd_migrate)
    assert res_migrate.is_ok
    migration = res_migrate.value()
    assert migration.status == "completed"
    assert migration.reindex_completed is True
    assert migration.source_version_id == "text-embedding-004"
    assert migration.target_version_id == "text-embedding-3-small"
    
    # Verify source policy updated
    updated_source = await source_repo.get_by_id(source.id)
    assert updated_source.policy.embedding_model == "text-embedding-3-small"
    
    # Verify chunks updated to new version ID and old ones deleted
    chunks_after = await chunk_repo.list_by_org("org_abc")
    assert len(chunks_after) > 0
    for chunk in chunks_after:
        assert chunk.embedding_version_id == "v_text-embedding-3-small"
