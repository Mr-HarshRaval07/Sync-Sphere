from beanie import Document
from pydantic import Field
from typing import List, Dict, Any, Optional
from syncsphere.shared_kernel.infrastructure.mongodb.base_document import BaseTenantDocument

class PromptExecutionDocument(BaseTenantDocument):
    """Beanie representation of PromptExecution telemetry audit log."""
    model_id: str
    provider_name: str
    prompt_template_id: Optional[str] = None
    version: Optional[int] = None
    system_prompt: Optional[str] = None
    user_prompt: Optional[str] = None
    response_text: Optional[str] = None
    latency_ms: float = 0.0
    
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    
    prompt_cost: float = 0.0
    completion_cost: float = 0.0
    total_cost: float = 0.0
    
    cache_hit: bool = False
    circuit_breaker_status: str = "CLOSED"
    retries_attempted: int = 0
    is_fallback: bool = False
    fallback_provider: Optional[str] = None
    
    correlation_id: Optional[str] = None

    class Settings:
        name = "prompt_executions"
        indexes = [
            "org_id",
            "model_id",
            "correlation_id"
        ]
