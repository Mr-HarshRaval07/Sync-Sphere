from pydantic import BaseModel
from typing import Optional, Dict, Any
from syncsphere.knowledge.domain.value_objects import RetrievalPolicy

class SearchKnowledgeQuery(BaseModel):
    org_id: str
    query: str
    policy: RetrievalPolicy = RetrievalPolicy.BALANCED
    top_k: int = 5
    namespace: Optional[str] = None
    correlation_id: Optional[str] = None

class SearchConversationQuery(BaseModel):
    org_id: str
    session_id: str
    correlation_id: Optional[str] = None

class SearchPlannerMemoryQuery(BaseModel):
    org_id: str
    planner_id: str
    correlation_id: Optional[str] = None

class SearchExecutionMemoryQuery(BaseModel):
    org_id: str
    execution_id: str
    correlation_id: Optional[str] = None

class SearchWorkflowMemoryQuery(BaseModel):
    org_id: str
    workflow_id: str
    correlation_id: Optional[str] = None

class SearchOrganizationMemoryQuery(BaseModel):
    org_id: str
    correlation_id: Optional[str] = None

class GetKnowledgeGraphQuery(BaseModel):
    org_id: str
    namespace: Optional[str] = None
    correlation_id: Optional[str] = None

class GetKnowledgeStatisticsQuery(BaseModel):
    org_id: str
    correlation_id: Optional[str] = None
