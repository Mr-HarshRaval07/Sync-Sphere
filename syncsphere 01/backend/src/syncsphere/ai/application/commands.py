from pydantic import Field
from typing import List, Dict, Any, Optional
from syncsphere.shared_kernel.types.contracts import BaseCommand
from syncsphere.ai.domain.value_objects import (
    ModelCapability,
    ModelSelectionPolicy,
    InferenceSettings,
    PromptVariable,
)

class RegisterProviderCommand(BaseCommand):
    org_id: str
    name: str
    api_key: str
    api_url_override: Optional[str] = None
    priority_level: int = 1
    config_meta: Dict[str, Any] = Field(default_factory=dict)

class RegisterModelCommand(BaseCommand):
    org_id: str
    provider_id: str
    name: str
    display_name: str
    capabilities: List[ModelCapability]
    context_window: int = 4096
    max_output_tokens: int = 2048
    cost_per_1k_input: float = 0.0
    cost_per_1k_output: float = 0.0

class EnableModelCommand(BaseCommand):
    org_id: str
    model_id: str

class DisableModelCommand(BaseCommand):
    org_id: str
    model_id: str

class RegisterPromptCommand(BaseCommand):
    org_id: str
    name: str
    description: Optional[str] = ""
    system_template: str
    user_template: str
    variables: List[PromptVariable] = Field(default_factory=list)

class UpdatePromptCommand(BaseCommand):
    org_id: str
    name: str
    system_template: str
    user_template: str
    description: Optional[str] = ""

class DeletePromptCommand(BaseCommand):
    org_id: str
    name: str

class GenerateEmbeddingCommand(BaseCommand):
    org_id: str
    input_texts: List[str]
    policy: ModelSelectionPolicy = ModelSelectionPolicy.EMBEDDING

class GenerateCompletionCommand(BaseCommand):
    org_id: str
    prompt: str
    policy: ModelSelectionPolicy = ModelSelectionPolicy.FAST
    settings: InferenceSettings = Field(default_factory=InferenceSettings)

class GenerateChatResponseCommand(BaseCommand):
    org_id: str
    messages: List[Dict[str, Any]]  # Standard list of dict format
    policy: ModelSelectionPolicy = ModelSelectionPolicy.FAST
    settings: InferenceSettings = Field(default_factory=InferenceSettings)

class EstimateTokensCommand(BaseCommand):
    org_id: str
    text: str
    model_name: Optional[str] = None

class EstimateCostCommand(BaseCommand):
    org_id: str
    prompt_tokens: int
    completion_tokens: int
    model_name: str

class ValidatePromptCommand(BaseCommand):
    org_id: str
    name: str
    variables: Dict[str, Any] = Field(default_factory=dict)
