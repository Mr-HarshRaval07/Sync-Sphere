from datetime import datetime
from typing import Optional, List
from syncsphere.shared_kernel.domain.entity import Entity
from syncsphere.knowledge.domain.value_objects import KnowledgeMetadata, KnowledgeRelationship

class KnowledgeDocument(Entity):
    """
    KnowledgeDocument holds the text contents, permissions namespaces,
    citations, and semantic relationship graph edges of a single parsed artifact.
    """
    
    def __init__(
        self,
        source_id: str,
        org_id: str,
        title: str,
        content: str,
        namespace: Optional[str] = None,
        status: str = "imported",  # imported, parsed, normalized, indexed, failed
        version: int = 1,
        metadata: Optional[KnowledgeMetadata] = None,
        relationships: Optional[List[KnowledgeRelationship]] = None,
        id: Optional[str] = None,
        **kwargs
    ) -> None:
        super().__init__(id=id, **kwargs)
        self.source_id = source_id
        self.org_id = org_id
        self.title = title
        self.content = content
        self.namespace = namespace or "default"
        self.status = status
        self.version = version
        self.metadata = metadata or KnowledgeMetadata()
        self.relationships = relationships or []

    def add_relationship(self, target_node_id: str, rel_type: str, weight: float = 1.0) -> None:
        relationship = KnowledgeRelationship(
            source_node_id=self.id,
            target_node_id=target_node_id,
            relationship_type=rel_type,
            weight=weight
        )
        self.relationships.append(relationship)
        self.updated_at = datetime.utcnow()
