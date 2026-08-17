from abc import ABC, abstractmethod
from typing import Optional, List
from syncsphere.ai.domain.entities.model import AIModel, ModelProvider
from syncsphere.ai.domain.entities.prompt import PromptTemplate, PromptVersion
from syncsphere.ai.domain.entities.execution import PromptExecution

class ModelProviderRepository(ABC):
    """Abstract interface defining persistence operations for ModelProvider."""
    @abstractmethod
    async def save(self, provider: ModelProvider) -> None:
        pass

    @abstractmethod
    async def get_by_id(self, provider_id: str) -> Optional[ModelProvider]:
        pass

    @abstractmethod
    async def get_by_name(self, org_id: str, name: str) -> Optional[ModelProvider]:
        pass

    @abstractmethod
    async def list_by_org(self, org_id: str) -> List[ModelProvider]:
        pass

    @abstractmethod
    async def delete(self, provider_id: str) -> None:
        pass


class AIModelRepository(ABC):
    """Abstract interface defining persistence operations for AIModel."""
    @abstractmethod
    async def save(self, model: AIModel) -> None:
        pass

    @abstractmethod
    async def get_by_id(self, model_id: str) -> Optional[AIModel]:
        pass

    @abstractmethod
    async def get_by_name(self, org_id: str, name: str) -> Optional[AIModel]:
        pass

    @abstractmethod
    async def list_by_org(self, org_id: str) -> List[AIModel]:
        pass

    @abstractmethod
    async def delete(self, model_id: str) -> None:
        pass


class PromptTemplateRepository(ABC):
    """Abstract interface defining persistence operations for PromptTemplate."""
    @abstractmethod
    async def save(self, template: PromptTemplate) -> None:
        pass

    @abstractmethod
    async def get_by_id(self, template_id: str) -> Optional[PromptTemplate]:
        pass

    @abstractmethod
    async def get_by_name(self, org_id: str, name: str) -> Optional[PromptTemplate]:
        pass

    @abstractmethod
    async def list_by_org(self, org_id: str, page: int, page_size: int) -> List[PromptTemplate]:
        pass

    @abstractmethod
    async def count_by_org(self, org_id: str) -> int:
        pass

    @abstractmethod
    async def delete(self, template_id: str) -> None:
        pass


class PromptVersionRepository(ABC):
    """Abstract interface defining persistence operations for PromptVersion snapshots."""
    @abstractmethod
    async def save(self, version: PromptVersion) -> None:
        pass

    @abstractmethod
    async def get_by_version(self, template_id: str, version: int) -> Optional[PromptVersion]:
        pass

    @abstractmethod
    async def list_versions(self, template_id: str) -> List[PromptVersion]:
        pass


class PromptExecutionRepository(ABC):
    """Abstract interface defining persistence operations for PromptExecution telemetry."""
    @abstractmethod
    async def save(self, execution: PromptExecution) -> None:
        pass

    @abstractmethod
    async def get_by_id(self, execution_id: str) -> Optional[PromptExecution]:
        pass

    @abstractmethod
    async def list_by_org(self, org_id: str, page: int, page_size: int) -> List[PromptExecution]:
        pass
