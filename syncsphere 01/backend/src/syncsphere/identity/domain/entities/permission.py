from typing import List, Optional
from pydantic import BaseModel, Field

class Permission(BaseModel):
    """
    Value Object representing a specific permission grant in SyncSphere.
    Immutable by design.
    """
    resource_type: str = Field(..., description="Type of resource: WORKFLOW, CONNECTOR, etc.")
    resource_id: str = Field(default="*", description="ID of specific resource or '*' for all")
    actions: List[str] = Field(default_factory=list, description="Allowed actions list, e.g. ['read', 'write']")

    def permits(self, resource_type: str, resource_id: str, action: str) -> bool:
        """Determines if this permission grants access to the specified resource & action."""
        if self.resource_type != resource_type:
            return False
        
        # Check resource_id wildcard or exact match
        if self.resource_id != "*" and self.resource_id != resource_id:
            return False
            
        return action in self.actions or "*" in self.actions
