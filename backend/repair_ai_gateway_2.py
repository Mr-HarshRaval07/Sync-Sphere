import sys, re

with open('src/syncsphere/ai/application/services/ai_gateway_impl.py', 'r') as f:
    c = f.read()

pattern = r'logger\.warning\("No DB fallback models available\. Engaging ultimate OpenRouter fallback\."\)\s+from syncsphere\.ai\.domain\.entities\.model import AIModel, ModelProvider\s+fallback_provider = ModelProvider\([^)]+\)\s+fallback_model = AIModel\([^)]+name="google/gemini-2\.5-flash"[^)]+\)\s+providers_dict\[fallback_provider\.id\] = fallback_provider'

repl = """from syncsphere.core.config.settings import settings
                if provider.name == settings.ai.llm_provider and model.name == settings.ai.llm_model:
                    raise primary_error
                    
                logger.warning("No DB fallback models available. Engaging ultimate default fallback.")
                from syncsphere.ai.domain.entities.model import AIModel, ModelProvider
                fallback_provider = ModelProvider(
                    id="ultimate_fallback_provider",
                    org_id=org_id,
                    name=settings.ai.llm_provider,
                    api_key_encrypted="dummy_encrypted_key",
                )
                fallback_model = AIModel(
                    id="ultimate_fallback_model",
                    org_id=org_id,
                    provider_id=fallback_provider.id,
                    name=settings.ai.llm_model,
                    display_name="System Default (Fallback)",
                    capabilities=[],
                )
                providers_dict[fallback_provider.id] = fallback_provider"""

c, count = re.subn(pattern, repl, c, flags=re.DOTALL)

with open('src/syncsphere/ai/application/services/ai_gateway_impl.py', 'w') as f:
    f.write(c)

print("Replaced", count)
