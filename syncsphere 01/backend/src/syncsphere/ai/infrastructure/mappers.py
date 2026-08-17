from typing import List
from syncsphere.ai.domain.entities.model import AIModel, ModelProvider
from syncsphere.ai.domain.entities.prompt import PromptTemplate, PromptVersion
from syncsphere.ai.domain.entities.execution import PromptExecution
from syncsphere.ai.domain.value_objects import (
    ModelCapability,
    ModelStatus,
    ModelLimits,
    ModelHealth,
    ProviderPriority,
    TokenUsage,
    CostUsage,
    PromptMetadata,
    PromptVariable,
)
from syncsphere.ai.infrastructure.documents import (
    ModelProviderDocument,
    AIModelDocument,
    PromptTemplateDocument,
    PromptVersionDocument,
    PromptExecutionDocument,
)

class AIMappers:
    """Translation utility between Domain aggregate entities and Beanie MongoDB documents."""
    
    @staticmethod
    def provider_to_domain(doc: ModelProviderDocument) -> ModelProvider:
        return ModelProvider(
            org_id=doc.org_id,
            name=doc.name,
            api_key_encrypted=doc.api_key_encrypted,
            api_url_override=doc.api_url_override,
            priority=ProviderPriority(
                priority_level=doc.priority_level,
                is_primary=doc.is_primary
            ),
            health=ModelHealth(
                is_healthy=doc.is_healthy,
                latency_ms=doc.latency_ms,
                error_message=doc.error_message
            ),
            status=ModelStatus(doc.status),
            config_meta=doc.config_meta,
            id=str(doc.id),
            created_at=doc.created_at,
            updated_at=doc.updated_at
        )

    @staticmethod
    def provider_to_document(domain: ModelProvider) -> ModelProviderDocument:
        return ModelProviderDocument(
            org_id=domain.org_id,
            name=domain.name,
            api_key_encrypted=domain.api_key_encrypted,
            api_url_override=domain.api_url_override,
            priority_level=domain.priority.priority_level,
            is_primary=domain.priority.is_primary,
            is_healthy=domain.health.is_healthy,
            latency_ms=domain.health.latency_ms,
            error_message=domain.health.error_message,
            status=domain.status.value,
            config_meta=domain.config_meta,
            created_at=domain.created_at,
            updated_at=domain.updated_at
        )

    @staticmethod
    def model_to_domain(doc: AIModelDocument) -> AIModel:
        return AIModel(
            org_id=doc.org_id,
            provider_id=doc.provider_id,
            name=doc.name,
            display_name=doc.display_name,
            capabilities=[ModelCapability(c) for c in doc.capabilities],
            limits=ModelLimits(
                context_window=doc.context_window,
                max_output_tokens=doc.max_output_tokens
            ),
            cost_per_1k_input=doc.cost_per_1k_input,
            cost_per_1k_output=doc.cost_per_1k_output,
            status=ModelStatus(doc.status),
            id=str(doc.id),
            created_at=doc.created_at,
            updated_at=doc.updated_at
        )

    @staticmethod
    def model_to_document(domain: AIModel) -> AIModelDocument:
        return AIModelDocument(
            org_id=domain.org_id,
            provider_id=domain.provider_id,
            name=domain.name,
            display_name=domain.display_name,
            capabilities=[c.value for c in domain.capabilities],
            context_window=domain.limits.context_window,
            max_output_tokens=domain.limits.max_output_tokens,
            cost_per_1k_input=domain.cost_per_1k_input,
            cost_per_1k_output=domain.cost_per_1k_output,
            status=domain.status.value,
            created_at=domain.created_at,
            updated_at=domain.updated_at
        )

    @staticmethod
    def template_to_domain(doc: PromptTemplateDocument) -> PromptTemplate:
        return PromptTemplate(
            org_id=doc.org_id,
            name=doc.name,
            description=doc.description,
            latest_version=doc.latest_version,
            metadata=PromptMetadata(tags=doc.tags, author=doc.author, purpose=doc.purpose),
            variables=[PromptVariable(**v) for v in doc.variables],
            id=str(doc.id),
            created_at=doc.created_at,
            updated_at=doc.updated_at
        )

    @staticmethod
    def template_to_document(domain: PromptTemplate) -> PromptTemplateDocument:
        return PromptTemplateDocument(
            org_id=domain.org_id,
            name=domain.name,
            description=domain.description,
            latest_version=domain.latest_version,
            tags=domain.metadata.tags,
            author=domain.metadata.author,
            purpose=domain.metadata.purpose,
            variables=[v.model_dump() for v in domain.variables],
            created_at=domain.created_at,
            updated_at=domain.updated_at
        )

    @staticmethod
    def version_to_domain(doc: PromptVersionDocument) -> PromptVersion:
        return PromptVersion(
            prompt_template_id=doc.prompt_template_id,
            version=doc.version,
            system_template=doc.system_template,
            user_template=doc.user_template,
            hash=doc.hash,
            description=doc.description,
            parent_version_id=doc.parent_version_id,
            id=str(doc.id),
            created_at=doc.created_at,
            updated_at=doc.updated_at
        )

    @staticmethod
    def version_to_document(domain: PromptVersion) -> PromptVersionDocument:
        return PromptVersionDocument(
            prompt_template_id=domain.prompt_template_id,
            version=domain.version,
            system_template=domain.system_template,
            user_template=domain.user_template,
            hash=domain.hash,
            description=domain.description,
            parent_version_id=domain.parent_version_id,
            created_at=domain.created_at,
            updated_at=domain.updated_at
        )

    @staticmethod
    def execution_to_domain(doc: PromptExecutionDocument) -> PromptExecution:
        return PromptExecution(
            org_id=doc.org_id,
            model_id=doc.model_id,
            provider_name=doc.provider_name,
            prompt_template_id=doc.prompt_template_id,
            version=doc.version,
            system_prompt=doc.system_prompt,
            user_prompt=doc.user_prompt,
            response_text=doc.response_text,
            latency_ms=doc.latency_ms,
            token_usage=TokenUsage(
                prompt_tokens=doc.prompt_tokens,
                completion_tokens=doc.completion_tokens,
                total_tokens=doc.total_tokens
            ),
            cost_usage=CostUsage(
                prompt_cost=doc.prompt_cost,
                completion_cost=doc.completion_cost,
                total_cost=doc.total_cost
            ),
            cache_hit=doc.cache_hit,
            circuit_breaker_status=doc.circuit_breaker_status,
            retries_attempted=doc.retries_attempted,
            is_fallback=doc.is_fallback,
            fallback_provider=doc.fallback_provider,
            id=str(doc.id),
            created_at=doc.created_at,
            updated_at=doc.updated_at
        )

    @staticmethod
    def execution_to_document(domain: PromptExecution) -> PromptExecutionDocument:
        return PromptExecutionDocument(
            org_id=domain.org_id,
            model_id=domain.model_id,
            provider_name=domain.provider_name,
            prompt_template_id=domain.prompt_template_id,
            version=domain.version,
            system_prompt=domain.system_prompt,
            user_prompt=domain.user_prompt,
            response_text=domain.response_text,
            latency_ms=domain.latency_ms,
            prompt_tokens=domain.token_usage.prompt_tokens,
            completion_tokens=domain.token_usage.completion_tokens,
            total_tokens=domain.token_usage.total_tokens,
            prompt_cost=domain.cost_usage.prompt_cost,
            completion_cost=domain.cost_usage.completion_cost,
            total_cost=domain.cost_usage.total_cost,
            cache_hit=domain.cache_hit,
            circuit_breaker_status=domain.circuit_breaker_status,
            retries_attempted=domain.retries_attempted,
            is_fallback=domain.is_fallback,
            fallback_provider=domain.fallback_provider,
            correlation_id=domain.correlation_id,
            created_at=domain.created_at,
            updated_at=domain.updated_at
        )
