from pydantic import Field, BaseModel
from typing import List, Optional
from syncsphere.shared_kernel.infrastructure.mongodb.base_document import BaseTenantDocument

class PermissionEmbed(BaseModel):
    """Embedded representation of Permission Value Object inside Role Document."""
    resource_type: str
    resource_id: str = "*"
    actions: List[str]

class RoleDocument(BaseTenantDocument):
    """Beanie ODM representation of the Role entity."""
    name: str = Field(..., description="Role key name")
    description: str = Field(default="", description="Role human description")
    is_system_role: bool = Field(default=False, description="Flag representing platform system-defined role")
    permissions: List[PermissionEmbed] = Field(default_factory=list, description="Array of permission grants")

    class Settings:
        name = "roles"
        indexes = [
            "org_id",
            ("org_id", "name")
        ]
        # Include parent indexes from BaseTenantDocument
        # merge_indexes = True is default in Beanie if we inherit, but let's declare explicitly.
