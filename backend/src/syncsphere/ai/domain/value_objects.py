from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from enum import Enum
from datetime import datetime

class ModelCapability(str, Enum):
    TEXT_GENERATION = "text_generation"
    VISION = "vision"
    EMBEDDING = "embedding"
    STREAMING = "streaming"
    TOOL_CALLING = "tool_calling"
    STRUCTURED_OUTPUT = "structured_output"
    REASONING = "reasoning"

class ModelSelectionPolicy(str, Enum):
    FAST = "fast"
    CHEAP = "cheap"
    REASONING = "reasoning"
    VISION = "vision"
    EMBEDDING = "embedding"
    TOOL_CALLING = "tool_calling"

class ModelStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    DEGRADED = "degraded"

class ModelLimits(BaseModel):
    context_window: int = Field(default=4096, ge=1)
    max_output_tokens: int = Field(default=2048, ge=0)
    requests_per_minute: Optional[int] = Field(default=None, ge=1)

class ModelHealth(BaseModel):
    is_healthy: bool = True
    latency_ms: float = 0.0
    last_checked: datetime = Field(default_factory=datetime.utcnow)
    error_message: Optional[str] = None

class ProviderPriority(BaseModel):
    priority_level: int = Field(default=1, ge=1)
    is_primary: bool = True
    weight: float = Field(default=1.0, ge=0.0)

class InferenceSettings(BaseModel):
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(default=None, ge=1)
    top_p: float = Field(default=1.0, ge=0.0, le=1.0)
    stop_sequences: List[str] = Field(default_factory=list)
    json_output: bool = False
    presence_penalty: float = Field(default=0.0, ge=-2.0, le=2.0)
    frequency_penalty: float = Field(default=0.0, ge=-2.0, le=2.0)

class TokenUsage(BaseModel):
    prompt_tokens: int = Field(default=0, ge=0)
    completion_tokens: int = Field(default=0, ge=0)
    total_tokens: int = Field(default=0, ge=0)

class CostUsage(BaseModel):
    prompt_cost: float = Field(default=0.0, ge=0.0)
    completion_cost: float = Field(default=0.0, ge=0.0)
    total_cost: float = Field(default=0.0, ge=0.0)

class StreamingChunk(BaseModel):
    delta_text: str = ""
    finish_reason: Optional[str] = None
    token_usage: Optional[TokenUsage] = None

class StructuredOutputSchema(BaseModel):
    schema_name: str
    json_schema: Dict[str, Any] = Field(default_factory=dict)
    strict: bool = True

class StructuredOutputResult(BaseModel):
    success: bool
    parsed_object: Optional[Dict[str, Any]] = None
    raw_output: str = ""
    error_message: Optional[str] = None
    provider_name: Optional[str] = None
    model_name: Optional[str] = None
    token_usage: Optional[TokenUsage] = None
    cost_usage: Optional[CostUsage] = None
    openrouter_http_ms: Optional[float] = None
    json_validation_ms: Optional[float] = None
    workflow_gen_ms: Optional[float] = None
    mongo_save_ms: Optional[float] = None

class PromptMetadata(BaseModel):
    tags: Dict[str, str] = Field(default_factory=dict)
    author: Optional[str] = None
    purpose: Optional[str] = None

class PromptContext(BaseModel):
    variables: Dict[str, Any] = Field(default_factory=dict)

class PromptVariable(BaseModel):
    name: str
    type: str = "string"  # string, number, boolean, object, array
    description: Optional[str] = None
    default_val: Optional[Any] = None
    required: bool = True

class EmbeddingVector(BaseModel):
    vector: List[float]

class EmbeddingRequest(BaseModel):
    input_texts: List[str]
    model_policy: ModelSelectionPolicy = ModelSelectionPolicy.EMBEDDING

class ChatResponse(BaseModel):
    message_content: str
    role: str = "assistant"
    model_name: str
    provider_name: str
    token_usage: TokenUsage = Field(default_factory=TokenUsage)
    cost_usage: CostUsage = Field(default_factory=CostUsage)

class CompletionResponse(BaseModel):
    text: str
    model_name: str
    provider_name: str
    token_usage: TokenUsage = Field(default_factory=TokenUsage)
    cost_usage: CostUsage = Field(default_factory=CostUsage)

class ToolCall(BaseModel):
    call_id: str
    tool_name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)

class ToolCallResult(BaseModel):
    call_id: str
    tool_name: str
    output: str
    is_error: bool = False

