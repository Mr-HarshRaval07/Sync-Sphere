import logging
from typing import List, Optional, Dict, Any
from syncsphere.shared_kernel.types.result import Result
from syncsphere.shared_kernel.domain.domain_exception import EntityNotFoundException, ValidationException
from syncsphere.ai.domain.entities.model import AIModel, ModelProvider
from syncsphere.ai.domain.value_objects import (
    ModelCapability,
    ModelStatus,
    ModelLimits,
    ProviderPriority,
    ModelHealth,
)
from syncsphere.ai.domain.repositories import (
    AIModelRepository,
    ModelProviderRepository,
)

logger = logging.getLogger("syncsphere.ai.application.services.ai_service")

class AIService:
    """
    AIService coordinates registrations, states enabling/disabling, and listings
    for providers and models.
    """
    def __init__(
        self,
        model_repo: AIModelRepository,
        provider_repo: ModelProviderRepository,
        event_bus: Any  # EventPublisher interface
    ) -> None:
        self.model_repo = model_repo
        self.provider_repo = provider_repo
        self.event_bus = event_bus

    async def register_provider(
        self,
        org_id: str,
        name: str,
        api_key_encrypted: str,
        api_url_override: Optional[str] = None,
        priority_level: int = 1,
        config_meta: Optional[Dict[str, Any]] = None
    ) -> Result[ModelProvider, Exception]:
        """Registers a new organization-scoped provider config."""
        logger.info("Registering provider %s for org: %s", name, org_id)
        
        # Check duplicate
        existing = await self.provider_repo.get_by_name(org_id, name)
        if existing:
            return Result.fail(ValidationException(
                code="DUPLICATE_PROVIDER",
                message=f"Provider '{name}' already exists in your organization."
            ))

        provider = ModelProvider(
            org_id=org_id,
            name=name,
            api_key_encrypted=api_key_encrypted,
            api_url_override=api_url_override,
            priority=ProviderPriority(priority_level=priority_level),
            config_meta=config_meta
        )
        await self.provider_repo.save(provider)
        return Result.ok(provider)

    async def register_model(
        self,
        org_id: str,
        provider_id: str,
        name: str,
        display_name: str,
        capabilities: List[ModelCapability],
        context_window: int = 4096,
        max_output_tokens: int = 2048,
        cost_per_1k_input: float = 0.0,
        cost_per_1k_output: float = 0.0
    ) -> Result[AIModel, Exception]:
        """Registers a new supported model under a registered provider."""
        logger.info("Registering model %s under provider %s", name, provider_id)
        print(f"DEBUG: register_model called for {name}")
        print(f"DEBUG: provider_repo type is {type(self.provider_repo)}")
        print(f"DEBUG: model_repo type is {type(self.model_repo)}")
        print(f"DEBUG: event_bus type is {type(self.event_bus)}")
        
        provider = await self.provider_repo.get_by_id(provider_id)
        if not provider or provider.org_id != org_id:
            return Result.fail(EntityNotFoundException("PROVIDER_NOT_FOUND", "Parent provider configuration not found."))

        # Check duplicate model
        existing = await self.model_repo.get_by_name(org_id, name)
        if existing:
            return Result.fail(ValidationException(
                code="DUPLICATE_MODEL",
                message=f"Model with identifier '{name}' is already registered."
            ))

        model = AIModel(
            org_id=org_id,
            provider_id=provider_id,
            name=name,
            display_name=display_name,
            capabilities=capabilities,
            limits=ModelLimits(context_window=context_window, max_output_tokens=max_output_tokens),
            cost_per_1k_input=cost_per_1k_input,
            cost_per_1k_output=cost_per_1k_output
        )
        await self.model_repo.save(model)
        
        # Publish Event
        from syncsphere.ai.domain.events import ModelRegistered
        event = ModelRegistered(
            org_id=org_id,
            correlation_id="model-registration",
            model_id=model.id,
            name=model.name,
            provider_id=provider_id
        )
        await self.event_bus.publish(event)
        
        return Result.ok(model)

    async def enable_model(self, org_id: str, model_id: str) -> Result[AIModel, Exception]:
        model = await self.model_repo.get_by_id(model_id)
        if not model or model.org_id != org_id:
            return Result.fail(EntityNotFoundException("MODEL_NOT_FOUND", "Model not found."))
            
        model.status = ModelStatus.ACTIVE
        await self.model_repo.save(model)
        return Result.ok(model)

    async def disable_model(self, org_id: str, model_id: str) -> Result[AIModel, Exception]:
        model = await self.model_repo.get_by_id(model_id)
        if not model or model.org_id != org_id:
            return Result.fail(EntityNotFoundException("MODEL_NOT_FOUND", "Model not found."))
            
        model.status = ModelStatus.INACTIVE
        await self.model_repo.save(model)
        return Result.ok(model)
