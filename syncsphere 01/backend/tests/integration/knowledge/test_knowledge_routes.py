import pytest
import asyncio
from fastapi.testclient import TestClient
from syncsphere.main import app
from syncsphere.core.dependency_injection.container import container

client = TestClient(app)

def test_knowledge_routes_integration_flow():
    # 1. Register and Login to get auth token
    register_payload = {
        "email": "knowledge_admin@acme.ai",
        "password": "supersecretpassword123!",
        "first_name": "Bob",
        "last_name": "Knowledge",
        "org_name": "Acme Knowledge Corp",
        "org_slug": "acme-knowledge-corp"
    }
    client.post("/v1/auth/register", json=register_payload)
    
    resp_login = client.post("/v1/auth/login", json={"email": "knowledge_admin@acme.ai", "password": "supersecretpassword123!"})
    access_token = resp_login.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # 2. Mock AI Gateway embedding generator inside container
    async def mock_generate_embedding(org_id, input_texts, correlation_id=None):
        return [[0.8, 0.1, 0.1] for _ in input_texts]
    container.ai_gateway.generate_embedding = mock_generate_embedding

    # 3. Hit POST /v1/knowledge/import
    import_payload = {
        "name": "Acme Core Docs",
        "type": "text",
        "config": {"text": "SyncSphere relies on agentic planning pipelines and enterprise execution runtimes."},
        "sync_strategy": "incremental"
    }
    resp_import = client.post(
        "/v1/knowledge/import",
        json=import_payload,
        headers=headers
    )
    assert resp_import.status_code == 201
    import_data = resp_import.json()["data"]
    assert import_data["source_id"] is not None
    assert import_data["status"] == "active"
    
    source_id = import_data["source_id"]

    # 4. Hit POST /v1/knowledge/search
    search_payload = {
        "query": "planning pipelines",
        "policy": "BalancedRetrieval",
        "top_k": 2
    }
    resp_search = client.post(
        "/v1/knowledge/search",
        json=search_payload,
        headers=headers
    )
    assert resp_search.status_code == 200
    search_data = resp_search.json()["data"]
    assert len(search_data["results"]) > 0
    assert "SyncSphere relies on" in search_data["results"][0]["citation"]["text_snippet"]

    # 5. Hit POST /v1/knowledge/graph
    resp_graph = client.post(
        "/v1/knowledge/graph",
        json={},
        headers=headers
    )
    assert resp_graph.status_code == 200
    graph_data = resp_graph.json()["data"]
    assert len(graph_data["nodes"]) > 0

    # 6. Hit GET /v1/knowledge/statistics
    resp_stats = client.get(
        "/v1/knowledge/statistics",
        headers=headers
    )
    assert resp_stats.status_code == 200
    stats_data = resp_stats.json()["data"]["statistics"]
    assert stats_data["total_sources"] == 1
    assert stats_data["total_documents"] == 1

    # 7. Hit POST /v1/knowledge/memory/conversation
    mem_conv_payload = {
        "session_id": "session_rag_1",
        "messages": [{"role": "assistant", "content": "Knowledge updated"}],
        "summary": "rag summary"
    }
    resp_mem_conv = client.post(
        "/v1/knowledge/memory/conversation",
        json=mem_conv_payload,
        headers=headers
    )
    assert resp_mem_conv.status_code == 200
    assert resp_mem_conv.json()["data"] is True

    # 8. Hit POST /v1/knowledge/memory/search to retrieve the conversation
    search_mem_payload = {
        "memory_type": "conversation",
        "resource_id": "session_rag_1"
    }
    resp_search_mem = client.post(
        "/v1/knowledge/memory/search",
        json=search_mem_payload,
        headers=headers
    )
    assert resp_search_mem.status_code == 200
    mem_search_data = resp_search_mem.json()["data"]["memory"]
    assert mem_search_data["summary"] == "rag summary"

    # 9. Hit POST /v1/knowledge/memory/workflow
    mem_wf_payload = {
        "workflow_id": "workflow_rag_1",
        "context_keys": {"var": 42},
        "statistics": {"success_rate": 1.0}
    }
    resp_mem_wf = client.post(
        "/v1/knowledge/memory/workflow",
        json=mem_wf_payload,
        headers=headers
    )
    assert resp_mem_wf.status_code == 200
    assert resp_mem_wf.json()["data"] is True
