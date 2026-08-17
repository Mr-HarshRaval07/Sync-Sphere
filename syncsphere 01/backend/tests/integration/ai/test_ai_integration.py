import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

from syncsphere.main import app


# ============================================================
# AI INTEGRATION TEST
# ============================================================

def test_ai_platform_endpoints_flow(client):
    """
    End-to-end AI platform API test.

    External AI providers are completely mocked.

    Verifies:
      - authentication
      - provider registration
      - model registration
      - model enable/disable
      - prompt creation/versioning/compilation
      - chat routing
      - completion routing
      - embedding routing
    """

    # ========================================================
    # 1. REGISTER
    # ========================================================

    print("\n=== 1. REGISTER START ===", flush=True)

    register_payload = {
        "email": "ai_admin@acme.ai",
        "password": "supersecretpassword123!",
        "first_name": "AI",
        "last_name": "Admin",
        "org_name": "ACME AI",
        "org_slug": "acme-ai",
    }

    resp = client.post(
        "/v1/auth/register",
        json=register_payload,
    )

    print(
        f"=== 1. REGISTER COMPLETE: {resp.status_code} ===",
        flush=True,
    )

    assert resp.status_code == 201, resp.text

    # ========================================================
    # 2. LOGIN
    # ========================================================

    print("=== 2. LOGIN START ===", flush=True)

    resp_login = client.post(
        "/v1/auth/login",
        json={
            "email": "ai_admin@acme.ai",
            "password": "supersecretpassword123!",
        },
    )

    print(
        f"=== 2. LOGIN COMPLETE: {resp_login.status_code} ===",
        flush=True,
    )

    assert resp_login.status_code == 200, resp_login.text

    login_data = resp_login.json()
    token = login_data["data"]["access_token"]

    headers = {
        "Authorization": f"Bearer {token}",
    }

    # ========================================================
    # 3. REGISTER MOCK PROVIDER
    # ========================================================

    print("=== 3. PROVIDER REGISTRATION START ===", flush=True)

    provider_payload = {
        "name": "mock",
        "api_key": "mock-api-key-value",
        "priority_level": 1,
    }

    resp_provider = client.post(
        "/v1/ai/providers",
        json=provider_payload,
        headers=headers,
    )

    print(
        f"=== 3. PROVIDER REGISTRATION COMPLETE: "
        f"{resp_provider.status_code} ===",
        flush=True,
    )

    assert resp_provider.status_code == 201, resp_provider.text

    provider_data = resp_provider.json()["data"]

    assert provider_data["name"] == "mock"

    provider_id = provider_data["id"]

    # ========================================================
    # 4. REGISTER TEXT MODEL
    # ========================================================

    print("=== 4. TEXT MODEL REGISTRATION START ===", flush=True)

    model_payload = {
        "provider_id": provider_id,
        "name": "mock-text-model",
        "display_name": "Mock Text Model",
        "capabilities": ["text_generation"],
        "context_window": 4096,
        "max_output_tokens": 2048,
        "cost_per_1k_input": 0.0015,
        "cost_per_1k_output": 0.002,
    }

    resp_model = client.post(
        "/v1/ai/models",
        json=model_payload,
        headers=headers,
    )

    print(
        f"=== 4. TEXT MODEL REGISTRATION COMPLETE: "
        f"{resp_model.status_code} ===",
        flush=True,
    )

    assert resp_model.status_code == 201, resp_model.text

    model_data = resp_model.json()["data"]

    assert model_data["name"] == "mock-text-model"

    model_id = model_data["id"]

    # ========================================================
    # 5. DISABLE MODEL
    # ========================================================

    print("=== 5. DISABLE MODEL START ===", flush=True)

    resp_disable = client.post(
        f"/v1/ai/models/{model_id}/disable",
        headers=headers,
    )

    print(
        f"=== 5. DISABLE MODEL COMPLETE: "
        f"{resp_disable.status_code} ===",
        flush=True,
    )

    assert resp_disable.status_code == 200, resp_disable.text
    assert resp_disable.json()["data"]["status"] == "inactive"

    # ========================================================
    # 6. ENABLE MODEL
    # ========================================================

    print("=== 6. ENABLE MODEL START ===", flush=True)

    resp_enable = client.post(
        f"/v1/ai/models/{model_id}/enable",
        headers=headers,
    )

    print(
        f"=== 6. ENABLE MODEL COMPLETE: "
        f"{resp_enable.status_code} ===",
        flush=True,
    )

    assert resp_enable.status_code == 200, resp_enable.text
    assert resp_enable.json()["data"]["status"] == "active"

    # ========================================================
    # 7. REGISTER EMBEDDING MODEL
    # ========================================================

    print("=== 7. EMBEDDING MODEL REGISTRATION START ===", flush=True)

    embed_model_payload = {
        "provider_id": provider_id,
        "name": "mock-embed-model",
        "display_name": "Mock Embedding Model",
        "capabilities": ["embedding"],
        "context_window": 8192,
        "max_output_tokens": 0,
        "cost_per_1k_input": 0.0001,
        "cost_per_1k_output": 0.0,
    }

    resp_embed_model = client.post(
        "/v1/ai/models",
        json=embed_model_payload,
        headers=headers,
    )

    print(
        f"=== 7. EMBEDDING MODEL REGISTRATION COMPLETE: "
        f"{resp_embed_model.status_code} ===",
        flush=True,
    )

    assert resp_embed_model.status_code == 201, resp_embed_model.text

    # ========================================================
    # 8. CREATE PROMPT
    # ========================================================

    print("=== 8. CREATE PROMPT START ===", flush=True)

    prompt_payload = {
        "name": "system_welcome",
        "description": "Greeting message template",
        "system_template": (
            "You are a friendly agent. Customer: {{customer}}."
        ),
        "user_template": (
            "Write greeting message for {{customer}} on plan {{plan}}."
        ),
        "variables": [
            {
                "name": "customer",
                "required": True,
            },
            {
                "name": "plan",
                "required": False,
                "default_val": "Basic",
            },
        ],
    }

    resp_prompt = client.post(
        "/v1/ai/prompts",
        json=prompt_payload,
        headers=headers,
    )

    print(
        f"=== 8. CREATE PROMPT COMPLETE: "
        f"{resp_prompt.status_code} ===",
        flush=True,
    )

    assert resp_prompt.status_code == 201, resp_prompt.text

    prompt_data = resp_prompt.json()["data"]

    assert prompt_data["name"] == "system_welcome"
    assert prompt_data["latest_version"] == 1

    # ========================================================
    # 9. UPDATE PROMPT -> VERSION 2
    # ========================================================

    print("=== 9. UPDATE PROMPT START ===", flush=True)

    update_payload = {
        "system_template": (
            "You are a friendly agent. Hello {{customer}}."
        ),
        "user_template": (
            "Welcome {{customer}} to the platform."
        ),
        "description": "Update welcoming message format",
    }

    resp_update = client.put(
        "/v1/ai/prompts/system_welcome",
        json=update_payload,
        headers=headers,
    )

    print(
        f"=== 9. UPDATE PROMPT COMPLETE: "
        f"{resp_update.status_code} ===",
        flush=True,
    )

    assert resp_update.status_code == 200, resp_update.text

    update_data = resp_update.json()["data"]

    assert update_data["version"] == 2

    # ========================================================
    # 10. COMPILE PROMPT
    # ========================================================

    print("=== 10. COMPILE PROMPT START ===", flush=True)

    compile_payload = {
        "variables": {
            "customer": "Alice",
            "plan": "Premium",
        },
        "version_num": 2,
    }

    resp_compile = client.post(
        "/v1/ai/prompts/system_welcome/compile",
        json=compile_payload,
        headers=headers,
    )

    print(
        f"=== 10. COMPILE PROMPT COMPLETE: "
        f"{resp_compile.status_code} ===",
        flush=True,
    )

    assert resp_compile.status_code == 200, resp_compile.text

    compile_data = resp_compile.json()["data"]

    assert compile_data["system"] == (
        "You are a friendly agent. Hello Alice."
    )

    assert compile_data["user"] == (
        "Welcome Alice to the platform."
    )

    # ========================================================
    # 11. CHAT
    # ========================================================

    print("=== 11. CHAT START ===", flush=True)

    chat_payload = {
        "messages": [
            {
                "role": "user",
                "content": "Hello agent",
            }
        ],
        "policy": "fast",
        "settings": {
            "temperature": 0.5,
        },
    }

    mock_chat_response = type(
        "MockChatResponse",
        (),
        {
            "message_content": "Hello from mock AI",
            "provider_name": "mock",
            "model_name": "mock-text-model",
        },
    )()

    with patch(
        "syncsphere.ai.application.services.ai_gateway_impl."
        "AIGatewayImpl.generate_chat",
        new=AsyncMock(
            return_value=mock_chat_response
        ),
    ):
        resp_chat = client.post(
            "/v1/ai/chat",
            json=chat_payload,
            headers=headers,
        )

    print(
        f"=== 11. CHAT COMPLETE: "
        f"{resp_chat.status_code} ===",
        flush=True,
    )

    assert resp_chat.status_code == 200, resp_chat.text

    chat_data = resp_chat.json()["data"]

    assert "content" in chat_data
    assert chat_data["provider"] == "mock"
    assert chat_data["model"] == "mock-text-model"

    # ========================================================
    # 12. COMPLETION
    # ========================================================

    print("=== 12. COMPLETION START ===", flush=True)

    completion_payload = {
        "prompt": "Write a quick poem",
        "policy": "cheap",
    }

    mock_completion_response = type(
        "MockCompletionResponse",
        (),
        {
            "text": "A quick mock poem",
            "provider_name": "mock",
            "model_name": "mock-text-model",
        },
    )()

    with patch(
        "syncsphere.ai.application.services.ai_gateway_impl."
        "AIGatewayImpl.generate_completion",
        new=AsyncMock(
            return_value=mock_completion_response
        ),
    ):
        resp_comp = client.post(
            "/v1/ai/completion",
            json=completion_payload,
            headers=headers,
        )

    print(
        f"=== 12. COMPLETION COMPLETE: "
        f"{resp_comp.status_code} ===",
        flush=True,
    )

    assert resp_comp.status_code == 200, resp_comp.text

    comp_data = resp_comp.json()["data"]

    assert "text" in comp_data
    assert comp_data["provider"] == "mock"

    # ========================================================
    # 13. EMBEDDINGS
    # ========================================================

    print("=== 13. EMBEDDINGS START ===", flush=True)

    embed_payload = {
        "input_texts": [
            "hello",
            "world",
        ],
    }

    mock_embeddings = [
        [0.0] * 1536,
        [0.0] * 1536,
    ]

    with patch(
        "syncsphere.ai.application.services.ai_gateway_impl."
        "AIGatewayImpl.generate_embedding",
        new=AsyncMock(
            return_value=mock_embeddings
        ),
    ):
        resp_embed = client.post(
            "/v1/ai/embeddings",
            json=embed_payload,
            headers=headers,
        )

    print(
        f"=== 13. EMBEDDINGS COMPLETE: "
        f"{resp_embed.status_code} ===",
        flush=True,
    )

    assert resp_embed.status_code == 200, resp_embed.text

    embed_data = resp_embed.json()["data"]

    assert "embeddings" in embed_data
    assert len(embed_data["embeddings"]) == 2
    assert len(embed_data["embeddings"][0]) == 1536

    print("=== AI INTEGRATION TEST PASSED ===", flush=True)