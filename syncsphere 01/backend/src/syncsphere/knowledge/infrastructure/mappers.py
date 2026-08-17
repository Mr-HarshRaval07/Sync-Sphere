from typing import Dict, Any, List
from syncsphere.knowledge.domain.entities.source import KnowledgeSource
from syncsphere.knowledge.domain.entities.document import KnowledgeDocument
from syncsphere.knowledge.domain.entities.chunk import KnowledgeChunk
from syncsphere.knowledge.domain.entities.cache_entry import SemanticCacheEntry
from syncsphere.knowledge.domain.value_objects import (
    KnowledgePolicy,
    KnowledgeMetadata,
    KnowledgeSourceType,
    KnowledgeRelationship
)
from syncsphere.knowledge.infrastructure.documents import (
    KnowledgeSourceDocument,
    KnowledgeDocumentDocument,
    KnowledgeChunkDocument,
    SemanticCacheEntryDocument
)

class KnowledgeMappers:
    @staticmethod
    def source_to_domain(doc: KnowledgeSourceDocument) -> KnowledgeSource:
        policy = KnowledgePolicy(**doc.policy) if doc.policy else KnowledgePolicy()
        metadata = KnowledgeMetadata(attributes=doc.metadata) if doc.metadata else KnowledgeMetadata()
        return KnowledgeSource(
            org_id=doc.org_id,
            name=doc.name,
            type=KnowledgeSourceType(doc.type),
            config=doc.config,
            policy=policy,
            sync_strategy=doc.sync_strategy,
            sync_schedule=doc.sync_schedule,
            status=doc.status,
            last_sync_at=doc.last_sync_at,
            metadata=metadata,
            id=str(doc.id),
            created_at=doc.created_at,
            updated_at=doc.updated_at
        )

    @staticmethod
    def source_to_document(domain: KnowledgeSource) -> KnowledgeSourceDocument:
        return KnowledgeSourceDocument(
            org_id=domain.org_id,
            name=domain.name,
            type=domain.type.value,
            config=domain.config,
            policy=domain.policy.model_dump(),
            sync_strategy=domain.sync_strategy,
            sync_schedule=domain.sync_schedule,
            status=domain.status,
            last_sync_at=domain.last_sync_at,
            metadata=domain.metadata.attributes,
            created_at=domain.created_at,
            updated_at=domain.updated_at
        )

    @staticmethod
    def document_to_domain(doc: KnowledgeDocumentDocument) -> KnowledgeDocument:
        metadata = KnowledgeMetadata(attributes=doc.metadata) if doc.metadata else KnowledgeMetadata()
        relationships = [
            KnowledgeRelationship(**r) for r in doc.relationships
        ] if doc.relationships else []
        return KnowledgeDocument(
            source_id=doc.source_id,
            org_id=doc.org_id,
            title=doc.title,
            content=doc.content,
            namespace=doc.namespace,
            status=doc.status,
            version=doc.version,
            metadata=metadata,
            relationships=relationships,
            id=str(doc.id),
            created_at=doc.created_at,
            updated_at=doc.updated_at
        )

    @staticmethod
    def document_to_document_doc(domain: KnowledgeDocument) -> KnowledgeDocumentDocument:
        relationships = [r.model_dump() for r in domain.relationships]
        return KnowledgeDocumentDocument(
            source_id=domain.source_id,
            org_id=domain.org_id,
            title=domain.title,
            content=domain.content,
            namespace=domain.namespace,
            status=domain.status,
            version=domain.version,
            metadata=domain.metadata.attributes,
            relationships=relationships,
            created_at=domain.created_at,
            updated_at=domain.updated_at
        )

    @staticmethod
    def chunk_to_domain(doc: KnowledgeChunkDocument) -> KnowledgeChunk:
        return KnowledgeChunk(
            document_id=doc.document_id,
            source_id=doc.source_id,
            org_id=doc.org_id,
            text=doc.text,
            token_count=doc.token_count,
            namespace=doc.namespace,
            embedding=doc.embedding,
            embedding_version_id=doc.embedding_version_id,
            index_status=doc.index_status,
            id=str(doc.id),
            created_at=doc.created_at,
            updated_at=doc.updated_at
        )

    @staticmethod
    def chunk_to_document(domain: KnowledgeChunk) -> KnowledgeChunkDocument:
        return KnowledgeChunkDocument(
            document_id=domain.document_id,
            source_id=domain.source_id,
            text=domain.text,
            token_count=domain.token_count,
            namespace=domain.namespace,
            embedding=domain.embedding,
            embedding_version_id=domain.embedding_version_id,
            index_status=domain.index_status,
            org_id=domain.org_id,
            created_at=domain.created_at,
            updated_at=domain.updated_at
        )

    @staticmethod
    def cache_to_domain(doc: SemanticCacheEntryDocument) -> SemanticCacheEntry:
        return SemanticCacheEntry(
            org_id=doc.org_id,
            query_text=doc.query_text,
            response_text=doc.response_text,
            embedding=doc.embedding,
            similarity_threshold=doc.similarity_threshold,
            namespace=doc.namespace,
            eviction_policy=doc.eviction_policy,
            hit_count=doc.hit_count,
            last_accessed_at=doc.last_accessed_at,
            id=str(doc.id),
            created_at=doc.created_at,
            updated_at=doc.updated_at
        )

    @staticmethod
    def cache_to_document(domain: SemanticCacheEntry) -> SemanticCacheEntryDocument:
        return SemanticCacheEntryDocument(
            org_id=domain.org_id,
            query_text=domain.query_text,
            response_text=domain.response_text,
            embedding=domain.embedding,
            similarity_threshold=domain.similarity_threshold,
            namespace=domain.namespace,
            eviction_policy=domain.eviction_policy,
            hit_count=domain.hit_count,
            last_accessed_at=domain.last_accessed_at,
            created_at=domain.created_at,
            updated_at=domain.updated_at
        )
