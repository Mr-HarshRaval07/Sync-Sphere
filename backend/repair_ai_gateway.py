import sys

with open('src/syncsphere/ai/application/services/ai_gateway_impl.py', 'r') as f:
    c = f.read()

# For generate_chat
target_chat = """            if not fallback_model:
                logger.warning("No DB fallback models available. Engaging ultimate OpenRouter fallback.")
                from syncsphere.ai.domain.entities.model import AIModel, ModelProvider
                fallback_provider = ModelProvider(
                    id="ultimate_fallback_provider",
                    org_id=org_id,
                    name="openrouter",
                    api_key_encrypted="dummy_encrypted_key",
                )
                fallback_model = AIModel(
                    id="ultimate_fallback_model",
                    org_id=org_id,
                    provider_id=fallback_provider.id,
                    name="google/gemini-2.5-flash",
                    display_name="Gemini Flash (Fallback)",
                    capabilities=[],
                )
                providers_dict[fallback_provider.id] = fallback_provider
                
            fallback_provider = providers_dict.get(fallback_model.provider_id)"""

replacement_chat = """            if not fallback_model:
                from syncsphere.core.config.settings import settings
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
                providers_dict[fallback_provider.id] = fallback_provider
                
            fallback_provider = providers_dict.get(fallback_model.provider_id)"""

target_raise_chat = """            except Exception as fallback_err:
                self.circuit_breaker.record_failure(fallback_provider.name)
                from syncsphere.ai.domain.exceptions import ModelNotFoundException
                raise ModelNotFoundException(fallback_model.name)"""

replacement_raise_chat = """            except Exception as fallback_err:
                self.circuit_breaker.record_failure(fallback_provider.name)
                raise fallback_err"""

# We just do replacing. Wait, some of target_chat is indented differently?
# No, it should be the same. 

c = c.replace(target_chat, replacement_chat)
c = c.replace(target_raise_chat, replacement_raise_chat)

with open('src/syncsphere/ai/application/services/ai_gateway_impl.py', 'w') as f:
    f.write(c)

print("Applied replacements:", c.count('raise fallback_err'))
