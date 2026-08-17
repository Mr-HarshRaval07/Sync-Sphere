import sys

with open('src/syncsphere/ai/application/services/ai_gateway_impl.py', 'r') as f:
    c = f.read()

target = """            if not fallback_model:
                logger.error(
                    "AI Error | Provider selected: %s | Configured model: %s | Fallback model: None | API key present: %s | Exact failure reason: %s",
                    provider.name, model.name, bool(api_key), str(primary_error)
                )
                from syncsphere.ai.domain.exceptions import ModelNotFoundException
                raise ModelNotFoundException(model.name)"""

repl = """            if not fallback_model:
                logger.warning("No DB fallback models available. Engaging ultimate OpenRouter fallback.")
                from syncsphere.ai.domain.entities.model import AIModel, ModelProvider
                fallback_provider = ModelProvider(id="ultimate_fallback_provider", org_id=org_id, name="openrouter", api_key_encrypted="dummy_encrypted_key")
                fallback_model = AIModel(id="ultimate_fallback_model", org_id=org_id, provider_id=fallback_provider.id, name="google/gemini-2.5-flash", display_name="Gemini Flash (Fallback)", capabilities=[])
                providers_dict[fallback_provider.id] = fallback_provider"""

c = c.replace(target, repl)

with open('src/syncsphere/ai/application/services/ai_gateway_impl.py', 'w') as f:
    f.write(c)

print("Replaced instances:", c.count('ultimate_fallback_provider'))
