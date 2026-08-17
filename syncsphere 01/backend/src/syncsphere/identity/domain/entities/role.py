from typing import List, Optional
from syncsphere.shared_kernel.domain.entity import Entity
from .permission import Permission

class Role(Entity):
    """
    Role domain entity representing a group of permission sets.
    """
    
    def __init__(
        self,
        org_id: str,
        name: str,
        description: Optional[str] = None,
        is_system_role: bool = False,
        permissions: Optional[List[Permission]] = None,
        id: Optional[str] = None,
        **kwargs
    ) -> None:
        super().__init__(id=id, **kwargs)
        self.org_id = org_id
        self.name = name
        self.description = description or ""
        self.is_system_role = is_system_role
        self.permissions: List[Permission] = permissions or []

    def has_permission(self, resource_type: str, resource_id: str, action: str) -> bool:
        """Evaluates permissions list to check if access is granted."""
        for permission in self.permissions:
            if permission.permits(resource_type, resource_id, action):
                return True
        return False

    def add_permission(self, permission: Permission) -> None:
        """Appends a permission grant if not already present."""
        if permission not in self.permissions:
            self.permissions.append(permission)
