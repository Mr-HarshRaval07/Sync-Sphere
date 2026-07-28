from typing import Optional
from syncsphere.shared_kernel.domain.entity import Entity
from syncsphere.ai.domain.value_objects import TokenUsage, CostUsage

class PromptExecution(Entity):
    """
    PromptExecution entity representing the audit/telemetry records for every model request.
    """
    def __init__(
        self,
        org_id: str,
        model_id: str,
        provider_name: str,
        prompt_template_id: Optional[str] = None,
        version: Optional[int] = None,
        system_prompt: Optional[str] = None,
        user_prompt: Optional[str] = None,
        response_text: Optional[str] = None,
        latency_ms: float = 0.0,
        token_usage: Optional[TokenUsage] = None,
        cost_usage: Optional[CostUsage] = None,
        cache_hit: bool = False,
        circuit_breaker_status: str = "CLOSED",
        retries_attempted: int = 0,
        is_fallback: bool = False,
        fallback_provider: Optional[str] = None,
        correlation_id: Optional[str] = None,
        id: Optional[str] = None,
        **kwargs
    ) -> None:
        super().__init__(id=id, **kwargs)
        self.org_id = org_id
        self.model_id = model_id
        self.provider_name = provider_name
        self.prompt_template_id = prompt_template_id
        self.version = version
        self.system_prompt = system_prompt
        self.user_prompt = user_prompt
        self.response_text = response_text
        self.latency_ms = latency_ms
        self.token_usage = token_usage or TokenUsage()
        self.cost_usage = cost_usage or CostUsage()
        self.cache_hit = cache_hit
        self.circuit_breaker_status = circuit_breaker_status
        self.retries_attempted = retries_attempted
        self.is_fallback = is_fallback
        self.fallback_provider = fallback_provider
        self.correlation_id = correlation_id
