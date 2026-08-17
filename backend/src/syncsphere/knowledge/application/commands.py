from pydantic import BaseModel
from typing import Dict, Any, Optional, List
from syncsphere.knowledge.domain.value_objects import KnowledgeSourceType, KnowledgePolicy

class ImportKnowledgeCommand(BaseModel):
    org_id: str
    name: str
    type: KnowledgeSourceType
    config: Dict[str, Any]
    policy: Optional[KnowledgePolicy] = None
    sync_strategy: str = "incremental"
    sync_schedule: Optional[str] = None
    correlation_id: Optional[str] = None

class DeleteKnowledgeCommand(BaseModel):
    org_id: str
    source_id: str
    correlation_id: Optional[str] = None

class UpdateKnowledgeCommand(BaseModel):
    org_id: str
    doc_id: str
    title: str
    content: str
    correlation_id: Optional[str] = None

class GenerateEmbeddingsCommand(BaseModel):
    org_id: str
    source_id: str
    texts: List[str]
    correlation_id: Optional[str] = None

class ReindexKnowledgeCommand(BaseModel):
    org_id: str
    source_id: str
    correlation_id: Optional[str] = None

class InvalidateCacheCommand(BaseModel):
    org_id: str
    query_text: Optional[str] = None  # None clears all for org
    correlation_id: Optional[str] = None

# Memory Commands
class StoreConversationMemoryCommand(BaseModel):
    org_id: str
    session_id: str
    messages: List[Dict[str, Any]]
    summary: Optional[str] = None
    correlation_id: Optional[str] = None

class StoreWorkflowMemoryCommand(BaseModel):
    org_id: str
    workflow_id: str
    context_keys: Dict[str, Any]
    statistics: Optional[Dict[str, Any]] = None
    correlation_id: Optional[str] = None

class MigrateEmbeddingsCommand(BaseModel):
    org_id: str
    source_id: str
    target_model_name: str
    correlation_id: Optional[str] = None
