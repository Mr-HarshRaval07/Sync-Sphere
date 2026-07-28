from typing import List, Optional
import hashlib
from syncsphere.shared_kernel.domain.aggregate_root import AggregateRoot
from syncsphere.shared_kernel.domain.entity import Entity
from syncsphere.ai.domain.value_objects import PromptMetadata, PromptVariable

class PromptTemplate(AggregateRoot):
    """
    PromptTemplate represents the root configuration metadata for a versioned prompt.
    """
    def __init__(
        self,
        org_id: str,
        name: str,
        description: Optional[str] = "",
        latest_version: int = 0,
        metadata: Optional[PromptMetadata] = None,
        variables: Optional[List[PromptVariable]] = None,
        id: Optional[str] = None,
        **kwargs
    ) -> None:
        super().__init__(id=id, **kwargs)
        self.org_id = org_id
        self.name = name.strip()
        self.description = description
        self.latest_version = latest_version
        self.metadata = metadata or PromptMetadata()
        self.variables = variables or []

    def create_version(
        self,
        system_template: str,
        user_template: str,
        description: Optional[str] = "",
        parent_version_id: Optional[str] = None
    ) -> "PromptVersion":
        """Increments version number and creates a new PromptVersion snapshot."""
        self.latest_version += 1
        
        # Calculate SHA256 content hash
        content_bytes = (system_template + user_template).encode("utf-8")
        content_hash = hashlib.sha256(content_bytes).hexdigest()
        
        return PromptVersion(
            prompt_template_id=self.id,
            version=self.latest_version,
            system_template=system_template,
            user_template=user_template,
            description=description,
            hash=content_hash,
            parent_version_id=parent_version_id
        )


class PromptVersion(Entity):
    """
    PromptVersion represents an immutable version snapshot of system/user templates.
    """
    def __init__(
        self,
        prompt_template_id: str,
        version: int,
        system_template: str,
        user_template: str,
        hash: str,
        description: Optional[str] = "",
        parent_version_id: Optional[str] = None,
        id: Optional[str] = None,
        **kwargs
    ) -> None:
        super().__init__(id=id, **kwargs)
        self.prompt_template_id = prompt_template_id
        self.version = version
        self.system_template = system_template
        self.user_template = user_template
        self.hash = hash
        self.description = description
        self.parent_version_id = parent_version_id
