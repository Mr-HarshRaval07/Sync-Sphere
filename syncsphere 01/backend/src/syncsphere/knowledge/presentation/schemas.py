from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from syncsphere.knowledge.domain.value_objects import (
    KnowledgeSourceType,
    KnowledgePolicy,
    RetrievalPolicy,
    KnowledgeSearchResult,
    KnowledgeGraphNode,
    KnowledgeGraphEdge,
    KnowledgeStatistics
)

class ImportKnowledgeRequest(BaseModel):
    name: str = Field(..., min_length=1)
    type: KnowledgeSourceType
    config: Dict[str, Any]
    policy: Optional[KnowledgePolicy] = None
    sync_strategy: str = "incremental"
    sync_schedule: Optional[str] = None

class ImportKnowledgeResponse(BaseModel):
    source_id: str
    status: str

class ReindexKnowledgeRequest(BaseModel):
    source_id: str

class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    policy: RetrievalPolicy = RetrievalPolicy.BALANCED
    top_k: int = 5
    namespace: Optional[str] = None

class SearchResponse(BaseModel):
    results: List[KnowledgeSearchResult] = Field(default_factory=list)

class GetGraphRequest(BaseModel):
    namespace: Optional[str] = None

class GraphResponse(BaseModel):
    nodes: List[KnowledgeGraphNode] = Field(default_factory=list)
    edges: List[KnowledgeGraphEdge] = Field(default_factory=list)

class StatisticsResponse(BaseModel):
    statistics: KnowledgeStatistics

class SearchMemoryRequest(BaseModel):
    memory_type: str
    resource_id: str

class SearchMemoryResponse(BaseModel):
    memory: Optional[Dict[str, Any]] = None

class StoreConversationRequest(BaseModel):
    session_id: str
    messages: List[Dict[str, Any]] = Field(default_factory=list)
    summary: Optional[str] = None

class StoreWorkflowMemoryRequest(BaseModel):
    workflow_id: str
    context_keys: Dict[str, Any] = Field(default_factory=dict)
    statistics: Dict[str, Any] = Field(default_factory=dict)
