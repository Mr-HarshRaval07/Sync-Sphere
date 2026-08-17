from abc import ABC, abstractmethod
from typing import List, Optional, Dict
from syncsphere.ai.domain.entities.model import AIModel, ModelProvider
from syncsphere.ai.domain.value_objects import ModelCapability, ModelStatus

class ModelSelectionPolicyHandler(ABC):
    """Abstract selector policy mapping execution needs to the best active model."""
    
    @abstractmethod
    def select(self, models: List[AIModel], providers: Dict[str, ModelProvider]) -> Optional[AIModel]:
        pass

class FastPolicy(ModelSelectionPolicyHandler):
    """Selects the healthy model with the lowest provider latency."""
    def select(self, models: List[AIModel], providers: Dict[str, ModelProvider]) -> Optional[AIModel]:
        text_models = [
            m for m in models 
            if m.status == ModelStatus.ACTIVE 
            and m.has_capability(ModelCapability.TEXT_GENERATION)
        ]
        if not text_models:
            return None

        # Sort by provider health (healthy first) then provider latency
        def sort_key(model: AIModel):
            provider = providers.get(model.provider_id)
            if not provider:
                return (True, 999999.0) # Unwired provider
            health = provider.health
            # healthy first, then lower latency
            return (not health.is_healthy, health.latency_ms)

        text_models.sort(key=sort_key)
        return text_models[0]

class CheapPolicy(ModelSelectionPolicyHandler):
    """Selects the active text generation model with the lowest token costs."""
    def select(self, models: List[AIModel], providers: Dict[str, ModelProvider]) -> Optional[AIModel]:
        text_models = [
            m for m in models 
            if m.status == ModelStatus.ACTIVE 
            and m.has_capability(ModelCapability.TEXT_GENERATION)
        ]
        if not text_models:
            return None

        # Sort by cost per input token, then output token
        text_models.sort(key=lambda m: (m.cost_per_1k_input + m.cost_per_1k_output))
        return text_models[0]

class ReasoningPolicy(ModelSelectionPolicyHandler):
    """Selects reasoning capability models, preferring primary provider levels."""
    def select(self, models: List[AIModel], providers: Dict[str, ModelProvider]) -> Optional[AIModel]:
        reasoning_models = [
            m for m in models 
            if m.status == ModelStatus.ACTIVE 
            and m.has_capability(ModelCapability.REASONING)
        ]
        if not reasoning_models:
            # Fallback to general text generation if no specialized reasoning models
            reasoning_models = [
                m for m in models 
                if m.status == ModelStatus.ACTIVE 
                and m.has_capability(ModelCapability.TEXT_GENERATION)
            ]
        if not reasoning_models:
            return None

        # Sort by provider priority (lower priority_level number is higher priority)
        def sort_key(model: AIModel):
            provider = providers.get(model.provider_id)
            return provider.priority.priority_level if provider else 99

        reasoning_models.sort(key=sort_key)
        return reasoning_models[0]

class VisionPolicy(ModelSelectionPolicyHandler):
    """Selects models possessing computer vision capabilities."""
    def select(self, models: List[AIModel], providers: Dict[str, ModelProvider]) -> Optional[AIModel]:
        vision_models = [
            m for m in models 
            if m.status == ModelStatus.ACTIVE 
            and m.has_capability(ModelCapability.VISION)
        ]
        if not vision_models:
            return None
        return vision_models[0]

class EmbeddingPolicy(ModelSelectionPolicyHandler):
    """Selects embedding generation models."""
    def select(self, models: List[AIModel], providers: Dict[str, ModelProvider]) -> Optional[AIModel]:
        embed_models = [
            m for m in models 
            if m.status == ModelStatus.ACTIVE 
            and m.has_capability(ModelCapability.EMBEDDING)
        ]
        if not embed_models:
            return None
        return embed_models[0]

class ToolCallingPolicy(ModelSelectionPolicyHandler):
    """Selects active models supporting JSON schema tool invocations."""
    def select(self, models: List[AIModel], providers: Dict[str, ModelProvider]) -> Optional[AIModel]:
        tool_models = [
            m for m in models 
            if m.status == ModelStatus.ACTIVE 
            and m.has_capability(ModelCapability.TOOL_CALLING)
        ]
        if not tool_models:
            # Fallback to general text generation models
            tool_models = [
                m for m in models 
                if m.status == ModelStatus.ACTIVE 
                and m.has_capability(ModelCapability.TEXT_GENERATION)
            ]
        if not tool_models:
            return None
        return tool_models[0]
