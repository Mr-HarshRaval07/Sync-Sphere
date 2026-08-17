from abc import ABC, abstractmethod
from typing import Optional, List
from syncsphere.workflow.domain.entities.workflow_template import WorkflowTemplate

class WorkflowTemplateRepository(ABC):
    """Abstract Repository interface defining persistence operations for WorkflowTemplate blueprints."""
    
    @abstractmethod
    async def save(self, template: WorkflowTemplate) -> None:
        """Saves a workflow template blueprint in database."""
        pass

    @abstractmethod
    async def get_by_id(self, template_id: str) -> Optional[WorkflowTemplate]:
        """Retrieves a template by its primary ID."""
        pass

    @abstractmethod
    async def list_templates(self, category: Optional[str] = None) -> List[WorkflowTemplate]:
        """Lists all templates, optionally filtered by category."""
        pass
