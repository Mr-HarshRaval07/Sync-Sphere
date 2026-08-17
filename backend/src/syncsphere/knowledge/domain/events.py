from typing import List, Dict, Any, Optional
from syncsphere.core.events.base import BaseEvent

class KnowledgeImported(BaseEvent):
    event_type: str = "knowledge.imported"
    source_id: str
    documents_count: int

class KnowledgeIndexed(BaseEvent):
    event_type: str = "knowledge.indexed"
    source_id: str
    chunks_count: int

class KnowledgeUpdated(BaseEvent):
    event_type: str = "knowledge.updated"
    document_id: str
    version: int

class KnowledgeDeleted(BaseEvent):
    event_type: str = "knowledge.deleted"
    source_id: str

class EmbeddingGenerated(BaseEvent):
    event_type: str = "knowledge.embedding_generated"
    job_id: str
    chunks_count: int

class SearchExecuted(BaseEvent):
    event_type: str = "knowledge.search_executed"
    query: str
    policy: str
    results_count: int

class CacheHit(BaseEvent):
    event_type: str = "knowledge.cache_hit"
    query: str
    entry_id: str

class CacheMiss(BaseEvent):
    event_type: str = "knowledge.cache_miss"
    query: str

class ConversationStored(BaseEvent):
    event_type: str = "knowledge.conversation_stored"
    session_id: str

class MemoryUpdated(BaseEvent):
    event_type: str = "knowledge.memory_updated"
    memory_type: str
    resource_id: str

class KnowledgeGraphUpdated(BaseEvent):
    event_type: str = "knowledge.graph_updated"
    node_id: str
    edge_id: Optional[str] = None
