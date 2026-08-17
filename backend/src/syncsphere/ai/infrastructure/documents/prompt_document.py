from beanie import Document
from pydantic import Field
from typing import List, Dict, Any, Optional
from syncsphere.shared_kernel.infrastructure.mongodb.base_document import BaseTenantDocument

class PromptTemplateDocument(BaseTenantDocument):
    """Beanie representation of PromptTemplate."""
    name: str = Field(..., description="Unique prompt template lookup name")
    description: Optional[str] = ""
    latest_version: int = 0
    tags: Dict[str, str] = Field(default_factory=dict)
    author: Optional[str] = None
    purpose: Optional[str] = None
    variables: List[dict] = Field(default_factory=list)

    class Settings:
        name = "prompt_templates"
        indexes = [
            "org_id",
            ("org_id", "name")
        ]


class PromptVersionDocument(Document):
    """Beanie representation of PromptVersion snapshot."""
    prompt_template_id: str = Field(..., description="Parent template primary ID reference")
    version: int = Field(..., description="Snapshot version number")
    system_template: str = Field(..., description="System template text")
    user_template: str = Field(..., description="User template text")
    hash: str = Field(..., description="SHA256 signature hash of template text")
    description: Optional[str] = ""
    parent_version_id: Optional[str] = None

    class Settings:
        name = "prompt_versions"
        indexes = [
            "prompt_template_id",
            ("prompt_template_id", "version")
        ]
