import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, Request, status

from syncsphere.shared_kernel.infrastructure.http.responses import ResponseEnvelope, ResponseMeta
from syncsphere.shared_kernel.infrastructure.http.dependencies import verify_jwt
from syncsphere.shared_kernel.domain.domain_exception import EntityNotFoundException
from syncsphere.core.dependency_injection.container import container
from syncsphere.knowledge.presentation.schemas import (
    ImportKnowledgeRequest,
    ImportKnowledgeResponse,
    ReindexKnowledgeRequest,
    SearchRequest,
    SearchResponse,
    GetGraphRequest,
    GraphResponse,
    StatisticsResponse,
    SearchMemoryRequest,
    SearchMemoryResponse,
    StoreConversationRequest,
    StoreWorkflowMemoryRequest
)
from syncsphere.knowledge.application.commands import (
    ImportKnowledgeCommand,
    ReindexKnowledgeCommand,
    InvalidateCacheCommand,
    StoreConversationMemoryCommand,
    StoreWorkflowMemoryCommand
)
from syncsphere.knowledge.application.queries import (
    SearchKnowledgeQuery,
    SearchConversationQuery,
    SearchPlannerMemoryQuery,
    SearchWorkflowMemoryQuery,
    GetKnowledgeGraphQuery,
    GetKnowledgeStatisticsQuery
)

logger = logging.getLogger("syncsphere.knowledge.presentation.routes.knowledge_routes")

router = APIRouter(prefix="/knowledge", tags=["Knowledge"])

@router.get(
    "/sources",
    response_model=ResponseEnvelope[List[dict]],
    summary="List imported knowledge sources"
)
async def list_sources(
    request: Request,
    claims: dict = Depends(verify_jwt)
) -> dict:
    correlation_id = getattr(request.state, "correlation_id", None)
    org_id = claims["org"]
    
    sources = await container.knowledge_service.source_repo.list_by_org(org_id)
    data = [{
        "id": s.id,
        "name": s.name,
        "source_type": s.type.value if hasattr(s.type, "value") else str(s.type),
        "status": s.status,
        "chunk_count": s.statistics.get("total_chunks", 0) if s.statistics else 0
    } for s in sources]
    
    return {
        "data": data,
        "meta": ResponseMeta(request_id=correlation_id)
    }

@router.post(
    "/import",
    response_model=ResponseEnvelope[ImportKnowledgeResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Import data sources to knowledge index"
)
async def import_source(
    request: Request,
    body: ImportKnowledgeRequest,
    claims: dict = Depends(verify_jwt)
) -> dict:
    correlation_id = getattr(request.state, "correlation_id", None)
    org_id = claims["org"]
    
    cmd = ImportKnowledgeCommand(
        org_id=org_id,
        name=body.name,
        type=body.type,
        config=body.config,
        policy=body.policy,
        sync_strategy=body.sync_strategy,
        sync_schedule=body.sync_schedule,
        correlation_id=correlation_id
    )
    
    res = await container.knowledge_service.import_knowledge(cmd)
    if res.is_fail:
        raise res.error()
        
    source = res.value()
    return {
        "data": ImportKnowledgeResponse(
            source_id=source.id,
            status=source.status
        ),
        "meta": ResponseMeta(request_id=correlation_id)
    }

@router.post(
    "/reindex",
    response_model=ResponseEnvelope[bool],
    summary="Force reload reindexing for a source"
)
async def reindex_source(
    request: Request,
    body: ReindexKnowledgeRequest,
    claims: dict = Depends(verify_jwt)
) -> dict:
    correlation_id = getattr(request.state, "correlation_id", None)
    org_id = claims["org"]
    
    cmd = ReindexKnowledgeCommand(
        org_id=org_id,
        source_id=body.source_id,
        correlation_id=correlation_id
    )
    
    res = await container.knowledge_service.reindex_knowledge(cmd)
    if res.is_fail:
        raise res.error()
        
    return {
        "data": res.value(),
        "meta": ResponseMeta(request_id=correlation_id)
    }

@router.post(
    "/search",
    response_model=ResponseEnvelope[SearchResponse],
    summary="Semantic and Hybrid similarity search"
)
async def search_index(
    request: Request,
    body: SearchRequest,
    claims: dict = Depends(verify_jwt)
) -> dict:
    correlation_id = getattr(request.state, "correlation_id", None)
    org_id = claims["org"]
    
    query = SearchKnowledgeQuery(
        org_id=org_id,
        query=body.query,
        policy=body.policy,
        top_k=body.top_k,
        namespace=body.namespace,
        correlation_id=correlation_id
    )
    
    res = await container.knowledge_service.search_knowledge(query)
    if res.is_fail:
        raise res.error()
        
    context = res.value()
    # Map context citations to results schema
    results = []
    for citation in context.citations:
        results.append({
            "chunk_id": citation.reference.document_id,
            "document_id": citation.reference.document_id,
            "text": citation.text_snippet,
            "score": 0.9,  # placeholder hybrid score
            "citation": citation
        })
        
    return {
        "data": SearchResponse(results=results),
        "meta": ResponseMeta(request_id=correlation_id)
    }

@router.post(
    "/graph",
    response_model=ResponseEnvelope[GraphResponse],
    summary="Get visual node edges network map"
)
async def get_graph(
    request: Request,
    body: GetGraphRequest,
    claims: dict = Depends(verify_jwt)
) -> dict:
    correlation_id = getattr(request.state, "correlation_id", None)
    org_id = claims["org"]
    
    query = GetKnowledgeGraphQuery(
        org_id=org_id,
        namespace=body.namespace,
        correlation_id=correlation_id
    )
    
    res = await container.knowledge_service.get_knowledge_graph(query)
    if res.is_fail:
        raise res.error()
        
    graph = res.value()
    return {
        "data": GraphResponse(
            nodes=graph["nodes"],
            edges=graph["edges"]
        ),
        "meta": ResponseMeta(request_id=correlation_id)
    }

@router.get(
    "/statistics",
    response_model=ResponseEnvelope[StatisticsResponse],
    summary="Retrieve storage sizes statistics"
)
async def get_statistics(
    request: Request,
    claims: dict = Depends(verify_jwt)
) -> dict:
    correlation_id = getattr(request.state, "correlation_id", None)
    org_id = claims["org"]
    
    query = GetKnowledgeStatisticsQuery(
        org_id=org_id,
        correlation_id=correlation_id
    )
    
    res = await container.knowledge_service.get_statistics(query)
    if res.is_fail:
        raise res.error()
        
    return {
        "data": StatisticsResponse(statistics=res.value()),
        "meta": ResponseMeta(request_id=correlation_id)
    }

# Memory Endpoints
@router.post(
    "/memory/search",
    response_model=ResponseEnvelope[SearchMemoryResponse],
    summary="Query long-term conversational or planner memory context"
)
async def search_memory(
    request: Request,
    body: SearchMemoryRequest,
    claims: dict = Depends(verify_jwt)
) -> dict:
    correlation_id = getattr(request.state, "correlation_id", None)
    org_id = claims["org"]
    
    memory_type = body.memory_type.lower()
    res_data = None
    if memory_type == "conversation":
        res_data = await container.knowledge_service.memory_service.get_conversation_memory(org_id, body.resource_id)
    elif memory_type == "planner":
        res_data = await container.knowledge_service.memory_service.get_planner_memory(org_id, body.resource_id)
    elif memory_type == "execution":
        res_data = await container.knowledge_service.memory_service.get_execution_memory(org_id, body.resource_id)
    elif memory_type == "workflow":
        res_data = await container.knowledge_service.memory_service.get_workflow_memory(org_id, body.resource_id)
        
    return {
        "data": SearchMemoryResponse(memory=res_data),
        "meta": ResponseMeta(request_id=correlation_id)
    }

@router.post(
    "/memory/conversation",
    response_model=ResponseEnvelope[bool],
    summary="Store conversational messages memory payload"
)
async def save_conversation(
    request: Request,
    body: StoreConversationRequest,
    claims: dict = Depends(verify_jwt)
) -> dict:
    correlation_id = getattr(request.state, "correlation_id", None)
    org_id = claims["org"]
    
    cmd = StoreConversationMemoryCommand(
        org_id=org_id,
        session_id=body.session_id,
        messages=body.messages,
        summary=body.summary,
        correlation_id=correlation_id
    )
    
    res = await container.knowledge_service.store_conversation_memory(cmd)
    if res.is_fail:
        raise res.error()
        
    return {
        "data": res.value(),
        "meta": ResponseMeta(request_id=correlation_id)
    }

@router.post(
    "/memory/workflow",
    response_model=ResponseEnvelope[bool],
    summary="Store workflow context variables memory payload"
)
async def save_workflow(
    request: Request,
    body: StoreWorkflowMemoryRequest,
    claims: dict = Depends(verify_jwt)
) -> dict:
    correlation_id = getattr(request.state, "correlation_id", None)
    org_id = claims["org"]
    
    cmd = StoreWorkflowMemoryCommand(
        org_id=org_id,
        workflow_id=body.workflow_id,
        context_keys=body.context_keys,
        statistics=body.statistics,
        correlation_id=correlation_id
    )
    
    res = await container.knowledge_service.store_workflow_memory(cmd)
    if res.is_fail:
        raise res.error()
        
    return {
        "data": res.value(),
        "meta": ResponseMeta(request_id=correlation_id)
    }
