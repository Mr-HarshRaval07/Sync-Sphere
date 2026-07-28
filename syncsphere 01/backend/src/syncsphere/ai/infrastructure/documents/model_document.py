from beanie import Document
from pydantic import Field
from typing import List, Dict, Any, Optional
from syncsphere.shared_kernel.infrastructure.mongodb.base_document import BaseTenantDocument

class ModelProviderDocument(BaseTenantDocument):
    """Beanie representation of the ModelProvider aggregate."""
    name: str = Field(..., description="Provider name type, e.g. openai, gemini")
    api_key_encrypted: Optional[str] = Field(None, description="Encrypted credentials")
    api_url_override: Optional[str] = Field(None, description="Optional API endpoint URL override")
    
    priority_level: int = 1
    is_primary: bool = True
    
    is_healthy: bool = True
    latency_ms: float = 0.0
    last_checked: Optional[str] = None
    error_message: Optional[str] = None
    
    status: str = "active"
    config_meta: Dict[str, Any] = Field(default_factory=dict)

    class Settings:
        name = "ai_providers"
        indexes = [
            "org_id",
            ("org_id", "name")
        ]


class AIModelDocument(BaseTenantDocument):
    """Beanie representation of the AIModel aggregate."""
    provider_id: str = Field(..., description="Parent provider configuration primary ID")
    name: str = Field(..., description="Unique model identifier, e.g. gpt-4o")
    display_name: str = Field(..., description="Friendly model display name")
    capabilities: List[str] = Field(default_factory=list)
    
    context_window: int = 4096
    max_output_tokens: int = 2048
    
    cost_per_1k_input: float = 0.0
    cost_per_1k_output: float = 0.0
    
    status: str = "active"

    class Settings:
        name = "ai_models"
        indexes = [
            "org_id",
            ("org_id", "name"),
            ("org_id", "provider_id")
        ]
