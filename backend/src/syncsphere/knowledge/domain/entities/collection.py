from typing import Optional, List, Dict
from syncsphere.shared_kernel.domain.entity import Entity

class KnowledgeCollection(Entity):
    """
    KnowledgeCollection acts as a high-level grouping boundary around multiple namespaces,
    enforcing role-based access rules and metadata categorizations.
    """
    
    def __init__(
        self,
        org_id: str,
        name: str,
        description: Optional[str] = None,
        namespaces: Optional[List[str]] = None,
        permissions: Optional[Dict[str, List[str]]] = None,
        id: Optional[str] = None,
        **kwargs
    ) -> None:
        super().__init__(id=id, **kwargs)
        self.org_id = org_id
        self.name = name
        self.description = description or ""
        self.namespaces = namespaces or ["default"]
        self.permissions = permissions or {}  # role_id -> list of permissions (e.g. ["read", "write"])
