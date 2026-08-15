import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

from syncsphere.main import app

client = TestClient(app)


# ============================================================
# DETERMINISTIC AI RESPONSES
# ============================================================

async def mock_generate_chat(*args, **kwargs):
    return {
        "content": "Hello from mock AI",
        "provider": "mock",
        "model": "mock-text-model",
    }


async def mock_generate_completion(*args, **kwargs):
    return {
        "text": "A quick mock poem",
        "provider": "mock",
        "model": "mock-text-model",
    }


async def mock_generate_embedding(*args, **kwargs):
    return {
        "embeddings": [
            [0.0] * 1536,
            [0.0] * 1536,
        ],
        "provider": "mock",
        "model": "mock-embed-model",
    }


def test_ai_platform_endpoints_flow():
    """
    End-to-end AI platform API test.

    External AI providers are completely mocked.
    The test verifies:
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

    assert resp.status_code == 201, resp.text

    # ========================================================
    # 2. LOGIN
    # ========================================================

    resp_login = client.post(
        "/v1/auth/login",
        json={
            "email": "ai_admin@acme.ai",
            "password": "supersecretpassword123!",
        },
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

    assert resp_provider.status_code == 201, resp_provider.text

    provider_data = resp_provider.json()["data"]

    assert provider_data["name"] == "mock"

    provider_id = provider_data["id"]

    # ========================================================
    # 4. REGISTER TEXT MODEL
    # ========================================================

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

    assert resp_model.status_code == 201, resp_model.text

    model_data = resp_model.json()["data"]

    assert model_data["name"] == "mock-text-model"

    model_id = model_data["id"]

    # ========================================================
    # 5. DISABLE MODEL
    # ========================================================

    resp_disable = client.post(
        f"/v1/ai/models/{model_id}/disable",
        headers=headers,
    )

    assert resp_disable.status_code == 200, resp_disable.text
    assert resp_disable.json()["data"]["status"] == "inactive"

    # ========================================================
    # 6. ENABLE MODEL
    # ========================================================

    resp_enable = client.post(
        f"/v1/ai/models/{model_id}/enable",
        headers=headers,
    )

    assert resp_enable.status_code == 200, resp_enable.text
    assert resp_enable.json()["data"]["status"] == "active"

    # ========================================================
    # 7. REGISTER EMBEDDING MODEL
    # ========================================================

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

    assert resp_embed_model.status_code == 201, resp_embed_model.text

    # ========================================================
    # 8. CREATE PROMPT
    # ========================================================

    prompt_payload = {
        "name": "system_welcome",
        "description": "Greeting message template",
        "system_template": "You are a friendly agent. Customer: {{customer}}.",
        "user_template": "Write greeting message for {{customer}} on plan {{plan}}.",
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

    assert resp_prompt.status_code == 201, resp_prompt.text

    prompt_data = resp_prompt.json()["data"]

    assert prompt_data["name"] == "system_welcome"
    assert prompt_data["latest_version"] == 1

    # ========================================================
    # 9. UPDATE PROMPT -> VERSION 2
    # ========================================================

    update_payload = {
        "system_template": "You are a friendly agent. Hello {{customer}}.",
        "user_template": "Welcome {{customer}} to the platform.",
        "description": "Update welcoming message format",
    }

    resp_update = client.put(
        "/v1/ai/prompts/system_welcome",
        json=update_payload,
        headers=headers,
    )

    assert resp_update.status_code == 200, resp_update.text

    update_data = resp_update.json()["data"]

    assert update_data["version"] == 2

    # ========================================================
    # 10. COMPILE PROMPT
    # ========================================================

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

    # Patch the gateway method actually used by the route.
    with patch(
        "syncsphere.ai.application.services.ai_gateway_impl.AIGatewayImpl.generate_chat",
        new=AsyncMock(
            return_value=type(
                "MockChatResponse",
                (),
                {
                    "message_content": "Hello from mock AI",
                    "provider_name": "mock",
                    "model_name": "mock-text-model",
                },
            )(),
        ),
    ):
        resp_chat = client.post(
            "/v1/ai/chat",
            json=chat_payload,
            headers=headers,
        )

    assert resp_chat.status_code == 200, resp_chat.text

    chat_data = resp_chat.json()["data"]

    assert "content" in chat_data
    assert chat_data["provider"] == "mock"
    assert chat_data["model"] == "mock-text-model"

    # ========================================================
    # 12. COMPLETION
    # ========================================================

    completion_payload = {
        "prompt": "Write a quick poem",
        "policy": "cheap",
    }

    with patch(
        "syncsphere.ai.application.services.ai_gateway_impl.AIGatewayImpl.generate_completion",
        new=AsyncMock(
            return_value=type(
                "MockCompletionResponse",
                (),
                {
                    "text": "A quick mock poem",
                    "provider_name": "mock",
                    "model_name": "mock-text-model",
                },
            )(),
        ),
    ):
        resp_comp = client.post(
            "/v1/ai/completion",
            json=completion_payload,
            headers=headers,
        )

    assert resp_comp.status_code == 200, resp_comp.text

    comp_data = resp_comp.json()["data"]

    assert "text" in comp_data
    assert comp_data["provider"] == "mock"

    # ========================================================
    # 13. EMBEDDINGS
    # ========================================================

    embed_payload = {
        "input_texts": [
            "hello",
            "world",
        ],
    }

    with patch(
        "syncsphere.ai.application.services.ai_gateway_impl.AIGatewayImpl.generate_embedding",
        new=AsyncMock(
            return_value=[
                [0.0] * 1536,
                [0.0] * 1536,
            ],
        ),
    ):
        resp_embed = client.post(
            "/v1/ai/embeddings",
            json=embed_payload,
            headers=headers,
        )

    assert resp_embed.status_code == 200, resp_embed.text

    embed_data = resp_embed.json()["data"]

    assert "embeddings" in embed_data
    assert len(embed_data["embeddings"]) == 2
    assert len(embed_data["embeddings"][0]) == 1536