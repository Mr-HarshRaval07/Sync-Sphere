from typing import List, Dict, Any, Optional
from syncsphere.shared_kernel.domain.aggregate_root import AggregateRoot
from syncsphere.shared_kernel.domain.entity import Entity
from syncsphere.ai.domain.value_objects import (
    ModelCapability,
    ModelStatus,
    ModelLimits,
    ModelHealth,
    ProviderPriority,
)

class ModelProvider(AggregateRoot):
    """
    ModelProvider entity representing a configured AI inference provider instance
    scoped to an organization/tenant.
    """
    def __init__(
        self,
        org_id: str,
        name: str,
        api_key_encrypted: Optional[str] = None,
        api_url_override: Optional[str] = None,
        priority: Optional[ProviderPriority] = None,
        health: Optional[ModelHealth] = None,
        status: ModelStatus = ModelStatus.ACTIVE,
        config_meta: Optional[Dict[str, Any]] = None,
        id: Optional[str] = None,
        **kwargs
    ) -> None:
        super().__init__(id=id, **kwargs)
        self.org_id = org_id
        self.name = name.lower().strip()
        self.api_key_encrypted = api_key_encrypted
        self.api_url_override = api_url_override
        self.priority = priority or ProviderPriority()
        self.health = health or ModelHealth()
        self.status = status
        self.config_meta = config_meta or {}

    def update_health(self, is_healthy: bool, latency_ms: float, error_message: Optional[str] = None) -> None:
        """Updates the health status value object of the provider."""
        from datetime import datetime
        self.health = ModelHealth(
            is_healthy=is_healthy,
            latency_ms=latency_ms,
            last_checked=datetime.utcnow(),
            error_message=error_message
        )
        if not is_healthy:
            self.status = ModelStatus.DEGRADED
        else:
            self.status = ModelStatus.ACTIVE


class AIModel(Entity):
    """
    AIModel entity representing a specific machine learning model supported by a provider.
    """
    def __init__(
        self,
        org_id: str,
        provider_id: str,
        name: str,
        display_name: str,
        capabilities: List[ModelCapability],
        limits: Optional[ModelLimits] = None,
        cost_per_1k_input: float = 0.0,
        cost_per_1k_output: float = 0.0,
        status: ModelStatus = ModelStatus.ACTIVE,
        id: Optional[str] = None,
        **kwargs
    ) -> None:
        super().__init__(id=id, **kwargs)
        self.org_id = org_id
        self.provider_id = provider_id
        self.name = name.strip()
        self.display_name = display_name.strip()
        self.capabilities = capabilities
        self.limits = limits or ModelLimits()
        self.cost_per_1k_input = cost_per_1k_input
        self.cost_per_1k_output = cost_per_1k_output
        self.status = status

    def has_capability(self, capability: ModelCapability) -> bool:
        """Checks if the model has a requested execution capability."""
        return capability in self.capabilities

    def estimate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """Calculates input and output token costs."""
        input_cost = (prompt_tokens / 1000.0) * self.cost_per_1k_input
        output_cost = (completion_tokens / 1000.0) * self.cost_per_1k_output
        return input_cost + output_cost
