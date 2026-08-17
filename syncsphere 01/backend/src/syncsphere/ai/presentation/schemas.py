from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from syncsphere.ai.domain.value_objects import ModelCapability, ModelSelectionPolicy, InferenceSettings

class ProviderRegisterRequest(BaseModel):
    name: str = Field(..., example="openai")
    api_key: str = Field(..., example="sk-...")
    api_url_override: Optional[str] = Field(None, example="https://api.openai.com/v1")
    priority_level: int = Field(1, example=1)
    config_meta: Dict[str, Any] = Field(default_factory=dict)

class ModelRegisterRequest(BaseModel):
    provider_id: str = Field(..., example="60c72b2f9b1d8e2b8c8b4567")
    name: str = Field(..., example="gpt-4o")
    display_name: str = Field(..., example="GPT-4 Omni")
    capabilities: List[ModelCapability] = Field(..., example=["text_generation"])
    context_window: int = Field(4096, example=8192)
    max_output_tokens: int = Field(2048, example=4096)
    cost_per_1k_input: float = Field(0.0015, example=0.0015)
    cost_per_1k_output: float = Field(0.002, example=0.002)

class PromptRegisterRequest(BaseModel):
    name: str = Field(..., example="customer_welcome")
    description: Optional[str] = Field("", example="Welcome email prompt template")
    system_template: str = Field(..., example="You are a helpful customer service representative. Welcome {{customer_name}}.")
    user_template: str = Field(..., example="Create a welcome message for {{customer_name}} who signed up for {{plan_name}}.")
    variables: List[Dict[str, Any]] = Field(default_factory=list, example=[{"name": "customer_name", "required": True}])

class PromptUpdateRequest(BaseModel):
    system_template: str
    user_template: str
    description: Optional[str] = ""

class ChatMessageDTO(BaseModel):
    role: str = Field(..., example="user")
    content: str = Field(..., example="Hello, how can I use SyncSphere?")

class ChatGenerationRequest(BaseModel):
    messages: List[ChatMessageDTO]
    policy: ModelSelectionPolicy = Field(ModelSelectionPolicy.FAST)
    settings: InferenceSettings = Field(default_factory=InferenceSettings)
    correlation_id: Optional[str] = None

class CompletionGenerationRequest(BaseModel):
    prompt: str = Field(..., example="Translate the following to Spanish: Hello, World!")
    policy: ModelSelectionPolicy = Field(ModelSelectionPolicy.FAST)
    settings: InferenceSettings = Field(default_factory=InferenceSettings)
    correlation_id: Optional[str] = None

class EmbeddingGenerationRequest(BaseModel):
    input_texts: List[str] = Field(..., example=["Hello", "World"])
    correlation_id: Optional[str] = None

class PromptValidationRequest(BaseModel):
    variables: Dict[str, Any] = Field(default_factory=dict, example={"customer_name": "Alice"})

class PromptCompilationRequest(BaseModel):
    variables: Dict[str, Any] = Field(default_factory=dict, example={"customer_name": "Alice", "plan_name": "Pro"})
    version_num: Optional[int] = None
