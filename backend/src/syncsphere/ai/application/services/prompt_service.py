import logging
from typing import List, Optional, Any
from syncsphere.shared_kernel.types.result import Result
from syncsphere.shared_kernel.domain.domain_exception import EntityNotFoundException, ValidationException
from syncsphere.ai.domain.entities.prompt import PromptTemplate, PromptVersion
from syncsphere.ai.domain.value_objects import PromptMetadata, PromptVariable
from syncsphere.ai.domain.repositories import (
    PromptTemplateRepository,
    PromptVersionRepository,
)

logger = logging.getLogger("syncsphere.ai.application.services.prompt_service")

class PromptService:
    """
    PromptService coordinates CRUD operations and version snapshots management
    for versioned PromptTemplates.
    """
    def __init__(
        self,
        template_repo: PromptTemplateRepository,
        version_repo: PromptVersionRepository,
        event_bus: Any = None  # EventPublisher
    ) -> None:
        self.template_repo = template_repo
        self.version_repo = version_repo
        self.event_bus = event_bus

    async def create_prompt(
        self,
        org_id: str,
        name: str,
        system_template: str,
        user_template: str,
        description: Optional[str] = "",
        variables: Optional[List[PromptVariable]] = None,
        metadata: Optional[PromptMetadata] = None
    ) -> Result[PromptTemplate, Exception]:
        """Creates a prompt template and registers version 1 snapshot."""
        logger.info("Creating prompt: %s for org: %s", name, org_id)
        
        # Check duplicate
        existing = await self.template_repo.get_by_name(org_id, name)
        if existing:
            return Result.fail(ValidationException(
                code="DUPLICATE_PROMPT_NAME",
                message=f"Prompt with name '{name}' already exists in your organization."
            ))

        template = PromptTemplate(
            org_id=org_id,
            name=name,
            description=description,
            variables=variables,
            metadata=metadata
        )
        
        # Save template root to get ID
        await self.template_repo.save(template)
        
        # Create and save first version
        version = template.create_version(
            system_template=system_template,
            user_template=user_template,
            description="Initial version"
        )
        await self.version_repo.save(version)
        
        # Update template root latest version
        await self.template_repo.save(template)
        
        # Publish Event
        if self.event_bus:
            from syncsphere.ai.domain.events import PromptRegistered
            event = PromptRegistered(
                org_id=org_id,
                correlation_id="prompt-registration",
                template_id=template.id,
                name=template.name
            )
            await self.event_bus.publish(event)
            
        return Result.ok(template)

    async def update_prompt(
        self,
        org_id: str,
        name: str,
        system_template: str,
        user_template: str,
        description: Optional[str] = ""
    ) -> Result[PromptVersion, Exception]:
        """Creates a new version snapshot of an existing template."""
        template = await self.template_repo.get_by_name(org_id, name)
        if not template:
            return Result.fail(EntityNotFoundException("PROMPT_NOT_FOUND", "Prompt template not found."))

        version = template.create_version(
            system_template=system_template,
            user_template=user_template,
            description=description
        )
        await self.version_repo.save(version)
        await self.template_repo.save(template)
        
        # Publish Event
        if self.event_bus:
            from syncsphere.ai.domain.events import PromptUpdated
            event = PromptUpdated(
                org_id=org_id,
                correlation_id="prompt-update",
                template_id=template.id,
                name=template.name,
                version=version.version
            )
            await self.event_bus.publish(event)
            
        return Result.ok(version)

    async def delete_prompt(self, org_id: str, name: str) -> Result[bool, Exception]:
        template = await self.template_repo.get_by_name(org_id, name)
        if not template:
            return Result.fail(EntityNotFoundException("PROMPT_NOT_FOUND", "Prompt template not found."))
            
        await self.template_repo.delete(template.id)
        return Result.ok(True)
