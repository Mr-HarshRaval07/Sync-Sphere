from pydantic import Field
from syncsphere.core.events.base import BaseEvent

class PromptRegistered(BaseEvent):
    """Fired when a new prompt template is registered."""
    event_type: str = "ai.prompt_registered"
    template_id: str
    name: str

class PromptUpdated(BaseEvent):
    """Fired when a prompt template is updated with a new version."""
    event_type: str = "ai.prompt_updated"
    template_id: str
    name: str
    version: int

class ModelRegistered(BaseEvent):
    """Fired when a new model is registered."""
    event_type: str = "ai.model_registered"
    model_id: str
    name: str
    provider_id: str

class ProviderHealthy(BaseEvent):
    """Fired when a provider health check passes."""
    event_type: str = "ai.provider_healthy"
    provider_id: str
    provider_name: str
    latency_ms: float

class ProviderUnhealthy(BaseEvent):
    """Fired when a provider health check fails."""
    event_type: str = "ai.provider_unhealthy"
    provider_id: str
    provider_name: str
    error_message: str

class CompletionGenerated(BaseEvent):
    """Fired when a completion response is generated."""
    event_type: str = "ai.completion_generated"
    model_id: str
    tokens_prompt: int
    tokens_completion: int
    cost: float

class EmbeddingGenerated(BaseEvent):
    """Fired when text embeddings are generated."""
    event_type: str = "ai.embedding_generated"
    model_id: str
    tokens_prompt: int
    cost: float

class StreamingStarted(BaseEvent):
    """Fired when a completion streaming request starts."""
    event_type: str = "ai.streaming_started"
    model_id: str

class StreamingCompleted(BaseEvent):
    """Fired when a completion streaming request successfully completes."""
    event_type: str = "ai.streaming_completed"
    model_id: str
    tokens_prompt: int
    tokens_completion: int
    cost: float
