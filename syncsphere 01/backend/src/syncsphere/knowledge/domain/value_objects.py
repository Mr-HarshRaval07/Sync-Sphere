from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime

class KnowledgeSourceType(str, Enum):
    FILE = "file"
    URL = "url"
    TEXT = "text"
    CONNECTOR = "connector"

class ChunkingStrategy(str, Enum):
    FIXED_SIZE = "fixed_size"
    SENTENCE = "sentence"
    PARAGRAPH = "paragraph"
    MARKDOWN = "markdown"
    SEMANTIC = "semantic"
    CODE = "code"
    RECURSIVE = "recursive"
    TOKEN_BASED = "token_based"

class EmbeddingProviderType(str, Enum):
    OPENAI = "openai"
    GOOGLE = "google"
    ANTHROPIC = "anthropic"
    OLLAMA = "ollama"

class RetrievalPolicy(str, Enum):
    FAST = "FastRetrieval"
    BALANCED = "BalancedRetrieval"
    ACCURATE = "AccurateRetrieval"
    CHEAP = "CheapRetrieval"

class SearchType(str, Enum):
    SEMANTIC = "semantic"
    KEYWORD = "keyword"
    HYBRID = "hybrid"

class KnowledgeMetadata(BaseModel):
    attributes: Dict[str, Any] = Field(default_factory=dict)

class KnowledgeReference(BaseModel):
    document_id: str
    source_id: str
    title: str
    location: Optional[str] = None  # page number, heading, section
    uri: Optional[str] = None

class KnowledgeRelationship(BaseModel):
    source_node_id: str
    target_node_id: str
    relationship_type: str  # e.g., "REFERENCES", "DEPENDS_ON", "MEMBER_OF"
    weight: float = 1.0
    attributes: Dict[str, Any] = Field(default_factory=dict)

class KnowledgeGraphNode(BaseModel):
    node_id: str
    name: str
    type: str  # e.g., "ENTITY", "CONCEPT", "DOCUMENT"
    attributes: Dict[str, Any] = Field(default_factory=dict)

class KnowledgeGraphEdge(BaseModel):
    source_id: str
    target_id: str
    type: str
    weight: float = 1.0
    attributes: Dict[str, Any] = Field(default_factory=dict)

class KnowledgeSearchRequest(BaseModel):
    query: str
    policy: RetrievalPolicy = RetrievalPolicy.BALANCED
    top_k: int = 5
    filters: Dict[str, Any] = Field(default_factory=dict)
    namespace: Optional[str] = None

class KnowledgeCitation(BaseModel):
    citation_id: str
    text_snippet: str
    reference: KnowledgeReference

class KnowledgeSearchResult(BaseModel):
    chunk_id: str
    document_id: str
    text: str
    score: float  # Hybrid score combining semantic similarity and keyword scores
    citation: Optional[KnowledgeCitation] = None

class KnowledgeRanking(BaseModel):
    chunk_id: str
    semantic_score: float
    keyword_score: float
    combined_score: float

class KnowledgeContext(BaseModel):
    context_str: str
    citations: List[KnowledgeCitation] = Field(default_factory=list)

class EmbeddingVersion(BaseModel):
    version_id: str
    model_name: str
    dimensions: int
    created_at: datetime = Field(default_factory=datetime.utcnow)
    compatibility_fingerprint: str

class EmbeddingMigration(BaseModel):
    migration_id: str
    source_version_id: str
    target_version_id: str
    reindex_completed: bool = False
    status: str = "pending"  # pending, running, completed, failed
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

class KnowledgeRetentionPolicy(BaseModel):
    archive_after_days: int = 365
    delete_after_days: int = 730
    keep_versions: int = 3

class KnowledgePolicy(BaseModel):
    chunk_size: int = 512
    chunk_overlap: int = 64
    chunking_strategy: ChunkingStrategy = ChunkingStrategy.FIXED_SIZE
    embedding_model: str = "text-embedding-004"
    retrieval_policy: RetrievalPolicy = RetrievalPolicy.BALANCED
    retention_policy: KnowledgeRetentionPolicy = Field(default_factory=KnowledgeRetentionPolicy)

class KnowledgeStatistics(BaseModel):
    total_sources: int = 0
    total_documents: int = 0
    total_chunks: int = 0
    index_size_bytes: int = 0
    cache_hits: int = 0
    cache_misses: int = 0

# --- memory structures ---
class ConversationMemory(BaseModel):
    session_id: str
    messages: List[Dict[str, Any]] = Field(default_factory=list)
    summary: Optional[str] = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class PlannerMemory(BaseModel):
    planner_id: str
    goals_achieved: List[str] = Field(default_factory=list)
    decisions_trace: List[Dict[str, Any]] = Field(default_factory=list)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class ExecutionMemory(BaseModel):
    execution_id: str
    step_results: Dict[str, Any] = Field(default_factory=dict)
    state_snapshots: List[Dict[str, Any]] = Field(default_factory=list)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class WorkflowMemory(BaseModel):
    workflow_id: str
    context_keys: Dict[str, Any] = Field(default_factory=dict)
    statistics: Dict[str, Any] = Field(default_factory=dict)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class OrganizationMemory(BaseModel):
    org_id: str
    global_context: Dict[str, Any] = Field(default_factory=dict)
    vocabulary: List[str] = Field(default_factory=list)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class ConnectorMemory(BaseModel):
    connector_id: str
    schema_patterns: Dict[str, Any] = Field(default_factory=dict)
    failure_history: List[Dict[str, Any]] = Field(default_factory=list)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class SessionMemory(BaseModel):
    session_id: str
    variables: Dict[str, Any] = Field(default_factory=dict)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class UserMemory(BaseModel):
    user_id: str
    preferences: Dict[str, Any] = Field(default_factory=dict)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
