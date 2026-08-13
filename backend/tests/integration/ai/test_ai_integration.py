import pytest
from fastapi.testclient import TestClient
from syncsphere.main import app


def test_ai_platform_endpoints_flow():
    """
    Verifies registering provider/model configurations, setting up versioned prompts,
    compiling templates, and routing chat/completions/embeddings requests.
    """
    with TestClient(app) as client:
        # 1. Register org and user to get authenticated token
        register_payload = {
            "email": "ai_admin@acme.ai",
            "password": "supersecretpassword123!",
            "first_name": "AI",
            "last_name": "Admin",
            "org_name": "ACME AI",
            "org_slug": "acme-ai"
        }
        resp = client.post("/v1/auth/register", json=register_payload)
        assert resp.status_code == 201

        # Login
        resp_login = client.post("/v1/auth/login", json={
            "email": "ai_admin@acme.ai",
            "password": "supersecretpassword123!"
        })
        assert resp_login.status_code == 200
        token = resp_login.json()["data"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 2. Register mock AI model provider
        provider_payload = {
            "name": "mock",
            "api_key": "mock-api-key-value",
            "priority_level": 1
        }
        resp_provider = client.post("/v1/ai/providers", json=provider_payload, headers=headers)
        assert resp_provider.status_code == 201
        provider_data = resp_provider.json()["data"]
        assert provider_data["name"] == "mock"
        provider_id = provider_data["id"]

        # 3. Register model configurations under provider
        model_payload = {
            "provider_id": provider_id,
            "name": "mock-text-model",
            "display_name": "Mock Text Model",
            "capabilities": ["text_generation"],
            "context_window": 4096,
            "max_output_tokens": 2048,
            "cost_per_1k_input": 0.0015,
            "cost_per_1k_output": 0.002
        }
        print("--- POST /v1/ai/models (text) starting ---")
        resp_model = client.post("/v1/ai/models", json=model_payload, headers=headers)
        print(f"--- POST /v1/ai/models (text) completed: {resp_model.status_code} ---")
        assert resp_model.status_code == 201
        model_data = resp_model.json()["data"]
        assert model_data["name"] == "mock-text-model"
        model_id = model_data["id"]

        # Enable and disable model endpoints check
        print("--- POST disable starting ---")
        resp_disable = client.post(f"/v1/ai/models/{model_id}/disable", headers=headers)
        print(f"--- POST disable completed: {resp_disable.status_code} ---")
        assert resp_disable.status_code == 200
        assert resp_disable.json()["data"]["status"] == "inactive"

        print("--- POST enable starting ---")
        resp_enable = client.post(f"/v1/ai/models/{model_id}/enable", headers=headers)
        print(f"--- POST enable completed: {resp_enable.status_code} ---")
        assert resp_enable.status_code == 200
        assert resp_enable.json()["data"]["status"] == "active"

        # Register embedding model configuration
        embed_model_payload = {
            "provider_id": provider_id,
            "name": "mock-embed-model",
            "display_name": "Mock Embedding Model",
            "capabilities": ["embedding"],
            "context_window": 8192,
            "max_output_tokens": 0,
            "cost_per_1k_input": 0.0001,
            "cost_per_1k_output": 0.0
        }
        print("--- POST /v1/ai/models (embed) starting ---")
        resp_embed_model = client.post("/v1/ai/models", json=embed_model_payload, headers=headers)
        print(f"--- POST /v1/ai/models (embed) completed: {resp_embed_model.status_code} ---")
        assert resp_embed_model.status_code == 201

        # 4. Register Prompts Templates
        prompt_payload = {
            "name": "system_welcome",
            "description": "Greeting message template",
            "system_template": "You are a friendly agent. Customer: {{customer}}.",
            "user_template": "Write greeting message for {{customer}} on plan {{plan}}.",
            "variables": [
                {"name": "customer", "required": True},
                {"name": "plan", "required": False, "default_val": "Basic"}
            ]
        }
        resp_prompt = client.post("/v1/ai/prompts", json=prompt_payload, headers=headers)
        assert resp_prompt.status_code == 201
        prompt_data = resp_prompt.json()["data"]
        assert prompt_data["name"] == "system_welcome"
        assert prompt_data["latest_version"] == 1

        # Update template to produce version 2
        update_payload = {
            "system_template": "You are a friendly agent. Hello {{customer}}.",
            "user_template": "Welcome {{customer}} to the platform.",
            "description": "Update welcoming message format"
        }
        resp_update = client.put("/v1/ai/prompts/system_welcome", json=update_payload, headers=headers)
        assert resp_update.status_code == 200
        update_data = resp_update.json()["data"]
        assert update_data["version"] == 2

        # Compile Prompts template with variables
        compile_payload = {
            "variables": {
                "customer": "Alice",
                "plan": "Premium"
            },
            "version_num": 2
        }
        resp_compile = client.post("/v1/ai/prompts/system_welcome/compile", json=compile_payload, headers=headers)
        assert resp_compile.status_code == 200
        compile_data = resp_compile.json()["data"]
        assert compile_data["system"] == "You are a friendly agent. Hello Alice."
        assert compile_data["user"] == "Welcome Alice to the platform."

        # Validate prompt list and details endpoints
        resp_list = client.get("/v1/ai/prompts", headers=headers)
        assert resp_list.status_code == 200
        prompt_list = resp_list.json()["data"]
        assert any(item["name"] == "system_welcome" and item["versions_count"] == 2 for item in prompt_list)

        resp_get = client.get("/v1/ai/prompts/system_welcome", headers=headers)
        assert resp_get.status_code == 200
        prompt_detail = resp_get.json()["data"]
        assert prompt_detail["latest_version"] == 2
        assert len(prompt_detail["versions"]) == 2

        # 5. Route chat generation
        chat_payload = {
            "messages": [
                {"role": "user", "content": "Hello agent"}
            ],
            "policy": "fast",
            "settings": {
                "temperature": 0.5
            }
        }
        resp_chat = client.post("/v1/ai/chat", json=chat_payload, headers=headers)
        assert resp_chat.status_code == 200
        chat_data = resp_chat.json()["data"]
        assert "content" in chat_data
        assert chat_data["provider"] == "mock"
        assert chat_data["model"] == "mock-text-model"

        # Route completion generation
        completion_payload = {
            "prompt": "Write a quick poem",
            "policy": "cheap"
        }
        resp_comp = client.post("/v1/ai/completion", json=completion_payload, headers=headers)
        assert resp_comp.status_code == 200
        comp_data = resp_comp.json()["data"]
        assert "text" in comp_data
        assert comp_data["provider"] == "mock"

        # Route embedding generation
        embed_payload = {
            "input_texts": ["hello", "world"]
        }
        resp_embed = client.post("/v1/ai/embeddings", json=embed_payload, headers=headers)
        assert resp_embed.status_code == 200
        embed_data = resp_embed.json()["data"]
        assert "embeddings" in embed_data
        assert len(embed_data["embeddings"]) == 2
        assert len(embed_data["embeddings"][0]) == 1536
