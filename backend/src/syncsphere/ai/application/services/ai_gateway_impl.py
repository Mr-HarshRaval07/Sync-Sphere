import time
import logging
from typing import List, Dict, Any, Optional, AsyncGenerator

from syncsphere.shared_kernel.types.result import Result
from syncsphere.core.providers.secret import SecretProvider
from syncsphere.ai.domain.services.ai_gateway import AIGateway
from syncsphere.ai.domain.services.provider import AIProvider
from syncsphere.ai.domain.value_objects import (
    ModelSelectionPolicy,
    InferenceSettings,
    ChatResponse,
    CompletionResponse,
    StreamingChunk,
    StructuredOutputSchema,
    StructuredOutputResult,
    TokenUsage,
    CostUsage,
)
from syncsphere.ai.domain.entities.execution import PromptExecution
from syncsphere.ai.domain.repositories import (
    AIModelRepository,
    ModelProviderRepository,
    PromptExecutionRepository,
)
from syncsphere.ai.domain.exceptions import (
    ModelNotFoundException,
    ProviderOfflineException,
    InferenceQuotaExceededException,
)
from syncsphere.ai.application.services.policies import (
    FastPolicy,
    CheapPolicy,
    ReasoningPolicy,
    VisionPolicy,
    EmbeddingPolicy,
    ToolCallingPolicy,
    ModelSelectionPolicyHandler,
)
from syncsphere.ai.infrastructure.engine.circuit_breaker import CircuitBreaker
from syncsphere.ai.infrastructure.engine.rate_limiter import TenantRateLimiter
from syncsphere.ai.infrastructure.engine.cache import InferenceCache

logger = logging.getLogger("syncsphere.ai.application.services.ai_gateway_impl")

class AIGatewayImpl(AIGateway):
    """
    Implementation of the AIGateway interface coordinating model selection,
    credential decryption, fallback routing, rate limiting, circuit breaking,
    caching, telemetry auditing, and event bus integrations.
    """
    def __init__(
        self,
        model_repo: AIModelRepository,
        provider_repo: ModelProviderRepository,
        execution_repo: PromptExecutionRepository,
        secret_provider: SecretProvider,
        event_bus: Any,  # EventPublisher interface
        provider_registry: Dict[str, AIProvider],
        circuit_breaker: Optional[CircuitBreaker] = None,
        rate_limiter: Optional[TenantRateLimiter] = None,
        cache: Optional[InferenceCache] = None
    ) -> None:
        self.model_repo = model_repo
        self.provider_repo = provider_repo
        self.execution_repo = execution_repo
        self.secret_provider = secret_provider
        self.event_bus = event_bus
        self.provider_registry = provider_registry
        
        # Instantiate optional engine helper singletons if not injected
        self.circuit_breaker = circuit_breaker or CircuitBreaker()
        self.rate_limiter = rate_limiter or TenantRateLimiter()
        self.cache = cache or InferenceCache()
        
        # Initialize selection policies
        self.policies: Dict[ModelSelectionPolicy, ModelSelectionPolicyHandler] = {
            ModelSelectionPolicy.FAST: FastPolicy(),
            ModelSelectionPolicy.CHEAP: CheapPolicy(),
            ModelSelectionPolicy.REASONING: ReasoningPolicy(),
            ModelSelectionPolicy.VISION: VisionPolicy(),
            ModelSelectionPolicy.EMBEDDING: EmbeddingPolicy(),
            ModelSelectionPolicy.TOOL_CALLING: ToolCallingPolicy(),
        }

    async def _resolve_model_and_provider(
        self,
        org_id: str,
        policy: ModelSelectionPolicy
    ) -> tuple:
        """Resolves the best available AIModel and parent ModelProvider matching policy."""
        models = await self.model_repo.list_by_org(org_id)
        provider_list = await self.provider_repo.list_by_org(org_id)
        providers_dict = {p.id: p for p in provider_list}
        
        handler = self.policies.get(policy)
        if not handler:
            raise ValueError(f"Unsupported model selection policy: {policy}")
            
        selected_model = handler.select(models, providers_dict)
        if not selected_model:
            from syncsphere.core.config.settings import settings
            from syncsphere.ai.domain.entities.model import AIModel, ModelProvider
            from syncsphere.ai.domain.value_objects import ModelCapability
            
            # Use environment defaults for fallback if no DB records exist
            fallback_provider = ModelProvider(
                id="default_env_provider",
                org_id=org_id,
                name=settings.ai.llm_provider,
                api_key_encrypted="dummy_encrypted_key",
            )
            
            fallback_model = AIModel(
                id="ling-tiny-3.0",
                org_id=org_id,
                provider_id=fallback_provider.id,
                name=settings.ai.llm_model,
                display_name="Ling Tiny 3.0",
                capabilities=[ModelCapability.TEXT_GENERATION, ModelCapability.REASONING],
            )
            
            # Re-evaluate with fallback using the handler criteria
            selected_model = handler.select([fallback_model], {fallback_provider.id: fallback_provider})
            if not selected_model:
                raise ModelNotFoundException(f"No active model found matching policy '{policy}'")
            selected_provider = fallback_provider
        else:
            selected_provider = providers_dict.get(selected_model.provider_id)
            if not selected_provider:
                raise ModelNotFoundException(f"Provider not configured for model '{selected_model.name}'")
        
        return selected_model, selected_provider

    def _decrypt_api_key(self, provider: Any) -> str:
        """Decrypts the provider's API key strictly in-memory."""
        if not provider.api_key_encrypted or provider.api_key_encrypted == "dummy_encrypted_key":
            from syncsphere.core.config.settings import settings
            return settings.ai.llm_api_key.get_secret_value()
        return self.secret_provider.decrypt(provider.api_key_encrypted, provider.org_id)

    async def generate_chat(
        self,
        org_id: str,
        messages: List[Dict[str, Any]],
        policy: ModelSelectionPolicy,
        settings: Optional[InferenceSettings] = None,
        correlation_id: Optional[str] = None
    ) -> ChatResponse:
        settings = settings or InferenceSettings()
        correlation_id = correlation_id or "gateway-chat"
        
        # 1. Rate Limiting Check
        self.rate_limiter.check_limits(org_id, estimated_tokens=100) # conservative default estimation
        
        # 2. Cache check
        cached_result = self.cache.get(messages, settings)
        if cached_result and isinstance(cached_result, ChatResponse):
            # Telemetry audit log for cache hit
            execution = PromptExecution(
                org_id=org_id,
                model_id="cached",
                provider_name="cache",
                system_prompt=str(messages[0].get("content")) if messages else None,
                user_prompt=str(messages[-1].get("content")) if len(messages) > 1 else None,
                response_text=cached_result.message_content,
                latency_ms=0.0,
                token_usage=cached_result.token_usage,
                cost_usage=cached_result.cost_usage,
                cache_hit=True,
                correlation_id=correlation_id
            )
            await self.execution_repo.save(execution)
            return cached_result
            
        start_time = time.perf_counter()
        model, provider = await self._resolve_model_and_provider(org_id, policy)
        
        # 3. Circuit Breaker validation
        if not self.circuit_breaker.can_execute(provider.name):
            logger.warning("Circuit breaker is OPEN for provider '%s'. Routing directly to fallback.", provider.name)
            # Force primary error to trigger fallback routing logic
            raise ProviderOfflineException(provider.name, "Circuit breaker is currently OPEN.")

        adapter = self.provider_registry.get(provider.name)
        if not adapter:
            raise ProviderOfflineException(provider.name, "Provider adapter not registered in gateway.")
            
        api_key = self._decrypt_api_key(provider)
        retries = 0
        is_fallback = False
        fallback_name = None
        
        try:
            response = await adapter.generate_chat(
                model_name=model.name,
                messages=messages,
                settings=settings,
                api_key=api_key,
                api_url=provider.api_url_override
            )
            self.circuit_breaker.record_success(provider.name)
        except Exception as primary_error:
            self.circuit_breaker.record_failure(provider.name)
            
            # Fallback routing logic: find next best cheap model
            fallback_handler = CheapPolicy()
            all_models = await self.model_repo.list_by_org(org_id)
            all_providers = await self.provider_repo.list_by_org(org_id)
            providers_dict = {p.id: p for p in all_providers}
            
            # Filter out the failed model
            other_models = [m for m in all_models if m.id != model.id]
            fallback_model = fallback_handler.select(other_models, providers_dict)
            if not fallback_model:
                from syncsphere.core.config.settings import settings
                if provider.name == settings.ai.llm_provider and model.name == settings.ai.llm_model:
                    raise primary_error
                    
                logger.warning("No DB fallback models available. Engaging ultimate default fallback.")
                from syncsphere.ai.domain.entities.model import AIModel, ModelProvider
                fallback_provider = ModelProvider(id="ultimate_fallback_provider", org_id=org_id, name=settings.ai.llm_provider, api_key_encrypted="dummy_encrypted_key")
                fallback_model = AIModel(id="ultimate_fallback_model", org_id=org_id, provider_id=fallback_provider.id, name=settings.ai.llm_model, display_name="System Default (Fallback)", capabilities=[])
                providers_dict[fallback_provider.id] = fallback_provider
                
            fallback_provider = providers_dict.get(fallback_model.provider_id)
            
            logger.warning(
                "AI Fallback | Provider selected: %s | Configured model: %s | Fallback model: %s | API key present: %s | Exact failure reason: %s",
                provider.name, model.name, fallback_model.name, bool(api_key), str(primary_error)
            )
            
            # Check fallback circuit breaker
            if not self.circuit_breaker.can_execute(fallback_provider.name):
                from syncsphere.ai.domain.exceptions import ModelNotFoundException
                raise ModelNotFoundException(fallback_model.name)
                
            fallback_adapter = self.provider_registry.get(fallback_provider.name)
            if not fallback_adapter:
                from syncsphere.ai.domain.exceptions import ModelNotFoundException
                raise ModelNotFoundException(fallback_model.name)
                
            is_fallback = True
            fallback_name = fallback_provider.name
            retries += 1
            
            fallback_key = self._decrypt_api_key(fallback_provider)
            try:
                response = await fallback_adapter.generate_chat(
                    model_name=fallback_model.name,
                    messages=messages,
                    settings=settings,
                    api_key=fallback_key,
                    api_url=fallback_provider.api_url_override
                )
                self.circuit_breaker.record_success(fallback_provider.name)
            except Exception as fallback_err:
                self.circuit_breaker.record_failure(fallback_provider.name)
                raise fallback_err
                
            model = fallback_model
            provider = fallback_provider
            
        latency = (time.perf_counter() - start_time) * 1000.0
        
        # Store in cache
        self.cache.set(messages, settings, response)
        
        # Telemetry auditing
        execution = PromptExecution(
            org_id=org_id,
            model_id=model.id,
            provider_name=provider.name,
            system_prompt=str(messages[0].get("content")) if messages else None,
            user_prompt=str(messages[-1].get("content")) if len(messages) > 1 else None,
            response_text=response.message_content,
            latency_ms=latency,
            token_usage=response.token_usage,
            cost_usage=response.cost_usage,
            retries_attempted=retries,
            is_fallback=is_fallback,
            fallback_provider=fallback_name,
            correlation_id=correlation_id
        )
        await self.execution_repo.save(execution)
        
        try:
            from syncsphere.ai.domain.events import CompletionGenerated
            event = CompletionGenerated(
                org_id=org_id,
                correlation_id=correlation_id,
                model_id=model.id,
                tokens_prompt=response.token_usage.prompt_tokens,
                tokens_completion=response.token_usage.completion_tokens,
                cost=response.cost_usage.total_cost
            )
            await self.event_bus.publish(event)
        except Exception as event_err:
            logger.warning("Failed to publish AI telemetry event: %s", str(event_err))
        
        return response

    async def generate_completion(
        self,
        org_id: str,
        prompt: str,
        policy: ModelSelectionPolicy,
        settings: Optional[InferenceSettings] = None,
        correlation_id: Optional[str] = None
    ) -> CompletionResponse:
        settings = settings or InferenceSettings()
        correlation_id = correlation_id or "gateway-completion"
        
        self.rate_limiter.check_limits(org_id, estimated_tokens=100)
        
        cached_result = self.cache.get(prompt, settings)
        if cached_result and isinstance(cached_result, CompletionResponse):
            execution = PromptExecution(
                org_id=org_id,
                model_id="cached",
                provider_name="cache",
                user_prompt=prompt,
                response_text=cached_result.text,
                latency_ms=0.0,
                token_usage=cached_result.token_usage,
                cost_usage=cached_result.cost_usage,
                cache_hit=True,
                correlation_id=correlation_id
            )
            await self.execution_repo.save(execution)
            return cached_result
            
        start_time = time.perf_counter()
        model, provider = await self._resolve_model_and_provider(org_id, policy)
        
        if not self.circuit_breaker.can_execute(provider.name):
            raise ProviderOfflineException(provider.name, "Circuit breaker is OPEN.")

        adapter = self.provider_registry.get(provider.name)
        if not adapter:
            raise ProviderOfflineException(provider.name, "Provider adapter not registered in gateway.")
            
        api_key = self._decrypt_api_key(provider)
        retries = 0
        is_fallback = False
        fallback_name = None
        
        try:
            response = await adapter.generate_completion(
                model_name=model.name,
                prompt=prompt,
                settings=settings,
                api_key=api_key,
                api_url=provider.api_url_override
            )
            self.circuit_breaker.record_success(provider.name)
        except Exception as primary_error:
            self.circuit_breaker.record_failure(provider.name)
            
            fallback_handler = CheapPolicy()
            all_models = await self.model_repo.list_by_org(org_id)
            all_providers = await self.provider_repo.list_by_org(org_id)
            providers_dict = {p.id: p for p in all_providers}
            
            other_models = [m for m in all_models if m.id != model.id]
            fallback_model = fallback_handler.select(other_models, providers_dict)
            if not fallback_model:
                from syncsphere.core.config.settings import settings
                if provider.name == settings.ai.llm_provider and model.name == settings.ai.llm_model:
                    raise primary_error
                    
                logger.warning("No DB fallback models available. Engaging ultimate default fallback.")
                from syncsphere.ai.domain.entities.model import AIModel, ModelProvider
                fallback_provider = ModelProvider(id="ultimate_fallback_provider", org_id=org_id, name=settings.ai.llm_provider, api_key_encrypted="dummy_encrypted_key")
                fallback_model = AIModel(id="ultimate_fallback_model", org_id=org_id, provider_id=fallback_provider.id, name=settings.ai.llm_model, display_name="System Default (Fallback)", capabilities=[])
                providers_dict[fallback_provider.id] = fallback_provider
                
            fallback_provider = providers_dict.get(fallback_model.provider_id)
            
            logger.warning(
                "AI Fallback | Provider selected: %s | Configured model: %s | Fallback model: %s | API key present: %s | Exact failure reason: %s",
                provider.name, model.name, fallback_model.name, bool(api_key), str(primary_error)
            )
            
            if not self.circuit_breaker.can_execute(fallback_provider.name):
                from syncsphere.ai.domain.exceptions import ModelNotFoundException
                raise ModelNotFoundException(fallback_model.name)
                
            fallback_adapter = self.provider_registry.get(fallback_provider.name)
            if not fallback_adapter:
                from syncsphere.ai.domain.exceptions import ModelNotFoundException
                raise ModelNotFoundException(fallback_model.name)
            
            is_fallback = True
            fallback_name = fallback_provider.name
            retries += 1
            
            fallback_key = self._decrypt_api_key(fallback_provider)
            try:
                response = await fallback_adapter.generate_completion(
                    model_name=fallback_model.name,
                    prompt=prompt,
                    settings=settings,
                    api_key=fallback_key,
                    api_url=fallback_provider.api_url_override
                )
                self.circuit_breaker.record_success(fallback_provider.name)
            except Exception as fallback_err:
                self.circuit_breaker.record_failure(fallback_provider.name)
                raise fallback_err
                
            model = fallback_model
            provider = fallback_provider
            
        latency = (time.perf_counter() - start_time) * 1000.0
        
        self.cache.set(prompt, settings, response)
        
        # Persist audit log
        execution = PromptExecution(
            org_id=org_id,
            model_id=model.id,
            provider_name=provider.name,
            user_prompt=prompt,
            response_text=response.text,
            latency_ms=latency,
            token_usage=response.token_usage,
            cost_usage=response.cost_usage,
            retries_attempted=retries,
            is_fallback=is_fallback,
            fallback_provider=fallback_name,
            correlation_id=correlation_id
        )
        await self.execution_repo.save(execution)
        
        try:
            from syncsphere.ai.domain.events import CompletionGenerated
            event = CompletionGenerated(
                org_id=org_id,
                correlation_id=correlation_id,
                model_id=model.id,
                tokens_prompt=response.token_usage.prompt_tokens,
                tokens_completion=response.token_usage.completion_tokens,
                cost=response.cost_usage.total_cost
            )
            await self.event_bus.publish(event)
        except Exception as event_err:
            logger.warning("Failed to publish AI telemetry event: %s", str(event_err))
        
        return response

    async def generate_embedding(
        self,
        org_id: str,
        input_texts: List[str],
        correlation_id: Optional[str] = None
    ) -> List[List[float]]:
        correlation_id = correlation_id or "gateway-embed"
        
        self.rate_limiter.check_limits(org_id, estimated_tokens=len(input_texts)*10)
        
        start_time = time.perf_counter()
        model, provider = await self._resolve_model_and_provider(org_id, ModelSelectionPolicy.EMBEDDING)
        
        if not self.circuit_breaker.can_execute(provider.name):
            raise ProviderOfflineException(provider.name, "Circuit breaker is OPEN.")

        adapter = self.provider_registry.get(provider.name)
        if not adapter:
            raise ProviderOfflineException(provider.name, "Embedding adapter not registered.")
            
        api_key = self._decrypt_api_key(provider)
        
        try:
            vectors = await adapter.generate_embedding(
                model_name=model.name,
                input_texts=input_texts,
                api_key=api_key,
                api_url=provider.api_url_override
            )
            self.circuit_breaker.record_success(provider.name)
        except Exception as e:
            self.circuit_breaker.record_failure(provider.name)
            raise e
        
        latency = (time.perf_counter() - start_time) * 1000.0
        
        # Embedding Counter estimation
        word_count = sum(len(text.split()) for text in input_texts)
        est_tokens = int(word_count * 1.5)
        usage = TokenUsage(prompt_tokens=est_tokens, total_tokens=est_tokens)
        cost = CostUsage(prompt_cost=(est_tokens / 1000.0) * model.cost_per_1k_input)
        cost.total_cost = cost.prompt_cost
        
        execution = PromptExecution(
            org_id=org_id,
            model_id=model.id,
            provider_name=provider.name,
            latency_ms=latency,
            token_usage=usage,
            cost_usage=cost,
            correlation_id=correlation_id
        )
        await self.execution_repo.save(execution)
        
        try:
            from syncsphere.ai.domain.events import EmbeddingGenerated
            event = EmbeddingGenerated(
                org_id=org_id,
                correlation_id=correlation_id,
                model_id=model.id,
                tokens_prompt=est_tokens,
                cost=cost.total_cost
            )
            await self.event_bus.publish(event)
        except Exception as event_err:
            logger.warning("Failed to publish AI embedding telemetry event: %s", str(event_err))
        
        return vectors

    async def stream_completion(
        self,
        org_id: str,
        prompt: str,
        policy: ModelSelectionPolicy,
        settings: Optional[InferenceSettings] = None,
        correlation_id: Optional[str] = None
    ) -> AsyncGenerator[StreamingChunk, None]:
        settings = settings or InferenceSettings()
        correlation_id = correlation_id or "gateway-stream"
        
        self.rate_limiter.check_limits(org_id, estimated_tokens=100)
        
        model, provider = await self._resolve_model_and_provider(org_id, policy)
        
        if not self.circuit_breaker.can_execute(provider.name):
            raise ProviderOfflineException(provider.name, "Circuit breaker is OPEN.")

        adapter = self.provider_registry.get(provider.name)
        if not adapter:
            raise ProviderOfflineException(provider.name, "Streaming adapter not registered.")
            
        api_key = self._decrypt_api_key(provider)
        
        try:
            from syncsphere.ai.domain.events import StreamingStarted
            event_start = StreamingStarted(org_id=org_id, correlation_id=correlation_id, model_id=model.id)
            await self.event_bus.publish(event_start)
        except Exception as event_err:
            logger.warning("Failed to publish AI streaming start event: %s", str(event_err))
        
        total_text = ""
        chunk_count = 0
        start_time = time.perf_counter()
        
        try:
            async for chunk in adapter.stream_completion(
                model_name=model.name,
                prompt=prompt,
                settings=settings,
                api_key=api_key,
                api_url=provider.api_url_override
            ):
                total_text += chunk.delta_text
                chunk_count += 1
                yield chunk
            self.circuit_breaker.record_success(provider.name)
        except Exception as e:
            self.circuit_breaker.record_failure(provider.name)
            raise e
            
        latency = (time.perf_counter() - start_time) * 1000.0
        
        # Estimate usage
        prompt_est = int(len(prompt.split()) * 1.5)
        completion_est = int(len(total_text.split()) * 1.5)
        usage = TokenUsage(prompt_tokens=prompt_est, completion_tokens=completion_est, total_tokens=prompt_est + completion_est)
        cost_val = model.estimate_cost(prompt_est, completion_est)
        cost = CostUsage(
            prompt_cost=(prompt_est / 1000.0) * model.cost_per_1k_input,
            completion_cost=(completion_est / 1000.0) * model.cost_per_1k_output,
            total_cost=cost_val
        )
        
        # Telemetry
        execution = PromptExecution(
            org_id=org_id,
            model_id=model.id,
            provider_name=provider.name,
            user_prompt=prompt,
            response_text=total_text,
            latency_ms=latency,
            token_usage=usage,
            cost_usage=cost,
            correlation_id=correlation_id
        )
        await self.execution_repo.save(execution)
        
        try:
            from syncsphere.ai.domain.events import StreamingCompleted
            event_end = StreamingCompleted(
                org_id=org_id,
                correlation_id=correlation_id,
                model_id=model.id,
                tokens_prompt=prompt_est,
                tokens_completion=completion_est,
                cost=cost_val
            )
            await self.event_bus.publish(event_end)
        except Exception as event_err:
            logger.warning("Failed to publish AI streaming completed event: %s", str(event_err))

    async def structured_output(
        self,
        org_id: str,
        messages: List[Dict[str, Any]],
        schema: StructuredOutputSchema,
        policy: ModelSelectionPolicy,
        settings: Optional[InferenceSettings] = None,
        correlation_id: Optional[str] = None
    ) -> StructuredOutputResult:
        settings = settings or InferenceSettings()
        correlation_id = correlation_id or "gateway-structured"
        
        self.rate_limiter.check_limits(org_id, estimated_tokens=150)
        
        start_time = time.perf_counter()
        model, provider = await self._resolve_model_and_provider(org_id, policy)
        
        if not self.circuit_breaker.can_execute(provider.name):
            raise ProviderOfflineException(provider.name, "Circuit breaker is OPEN.")

        adapter = self.provider_registry.get(provider.name)
        if not adapter:
            raise ProviderOfflineException(provider.name, "Structured output adapter not registered.")
            
        api_key = self._decrypt_api_key(provider)
        
        # Validation Loop with Auto-Retry
        last_error = None
        current_messages = list(messages)
        
        try:
            for attempt in range(3):
                try:
                    result = await adapter.structured_output(
                        model_name=model.name,
                        messages=current_messages,
                        schema=schema,
                        settings=settings,
                        api_key=api_key,
                        api_url=provider.api_url_override
                    )
                    self.circuit_breaker.record_success(provider.name)
                    
                    if result.success:
                        latency = (time.perf_counter() - start_time) * 1000.0
                        
                        from syncsphere.ai.domain.value_objects import TokenUsage, CostUsage
                        from syncsphere.ai.domain.events import CompletionGenerated
                        
                        if result.token_usage and result.token_usage.total_tokens > 0:
                            tokens_prompt = result.token_usage.prompt_tokens
                            tokens_comp = result.token_usage.completion_tokens
                            cost_total = result.cost_usage.total_cost if result.cost_usage else 0.0
                            gateway_token_usage = result.token_usage
                            gateway_cost_usage = result.cost_usage or CostUsage()
                        else:
                            # Fallback: provider returned no usage (or all-zero) – estimate from content length
                            prompt_len = sum(len(str(m.get("content", ""))) for m in current_messages)
                            comp_len = len(result.raw_output or "")
                            tokens_prompt = max(prompt_len // 4, 1)
                            tokens_comp = max(comp_len // 4, 1)
                            cost_total = model.estimate_cost(tokens_prompt, tokens_comp)
                            gateway_token_usage = TokenUsage(prompt_tokens=tokens_prompt, completion_tokens=tokens_comp, total_tokens=tokens_prompt+tokens_comp)
                            gateway_cost_usage = CostUsage(prompt_cost=cost_total, completion_cost=0.0, total_cost=cost_total)
                            logger.info(
                                "Token usage not returned by provider %s - using estimation: prompt=%d, comp=%d, total=%d",
                                provider.name, tokens_prompt, tokens_comp, tokens_prompt + tokens_comp
                            )

                        mongo_save_start = time.perf_counter()
                        execution = PromptExecution(
                            org_id=org_id,
                            model_id=model.id,
                            provider_name=provider.name,
                            response_text=result.raw_output,
                            latency_ms=latency,
                            token_usage=gateway_token_usage,
                            cost_usage=gateway_cost_usage,
                            retries_attempted=attempt,
                            correlation_id=correlation_id
                        )
                        await self.execution_repo.save(execution)
                        result.mongo_save_ms = (time.perf_counter() - mongo_save_start) * 1000.0
                        
                        result.provider_name = provider.name
                        result.model_name = model.name
                        
                        try:
                            # Publish event
                            event = CompletionGenerated(
                                org_id=org_id,
                                correlation_id=correlation_id,
                                model_id=model.id,
                                tokens_prompt=tokens_prompt,
                                tokens_completion=tokens_comp,
                                cost=cost_total
                            )
                            await self.event_bus.publish(event)
                        except Exception as event_err:
                            # Soft fail telemetry so the main AI response does not crash and loop
                            logger.warning("Failed to publish AI telemetry event: %s", str(event_err))
                        
                        return result
                    else:
                        last_error = result.error_message
                        # Break immediately if this is an upstream Quota exhaustion or 429, not a JSON schema logic failure
                        if "429" in result.error_message or "quota" in result.error_message.lower():
                            break
                            
                        # Auto-retry on malformed outputs: append the failed output and the error message to instructions
                        current_messages.append({"role": "assistant", "content": result.raw_output})
                        current_messages.append({
                            "role": "user", 
                            "content": f"Your output violated the JSON schema. Error: {result.error_message}. Please correct the output and return valid JSON conforming to the schema."
                        })
                except Exception as e:
                    import asyncio
                    if isinstance(e, (asyncio.CancelledError, KeyboardInterrupt)):
                        raise e
                    last_error = str(e)
                    if isinstance(e, ProviderOfflineException) or "429" in str(e) or "quota" in str(e).lower() or "timeout" in str(e).lower():
                        self.circuit_breaker.record_failure(provider.name, reason=last_error)
                        raise ProviderOfflineException(provider.name, last_error)

                    current_messages.append({
                        "role": "user",
                        "content": f"An error occurred parsing structured JSON: {str(e)}. Please correct your format."
                    })
                    
            # If all validation retry loops fail
            return StructuredOutputResult(
                success=False,
                raw_output="",
                error_message=f"Auto-retry validation loop failed. Last error: {last_error}"
            )
            
        except Exception as primary_error:
            import asyncio
            if isinstance(primary_error, (asyncio.CancelledError, KeyboardInterrupt)):
                raise primary_error
            
            # Record failure on circuit breaker only for true provider infrastructure errors
            if "Circuit breaker" not in str(primary_error):
                if isinstance(primary_error, ProviderOfflineException) or "429" in str(primary_error) or "quota" in str(primary_error).lower() or "timeout" in str(primary_error).lower():
                    self.circuit_breaker.record_failure(provider.name, reason=str(primary_error))
            
            fallback_handler = CheapPolicy()
            all_models = await self.model_repo.list_by_org(org_id)
            all_providers = await self.provider_repo.list_by_org(org_id)
            providers_dict = {p.id: p for p in all_providers}
            
            other_models = [m for m in all_models if m.id != model.id]
            fallback_model = fallback_handler.select(other_models, providers_dict)
            if not fallback_model:
                from syncsphere.core.config.settings import settings
                if provider.name == settings.ai.llm_provider and model.name == settings.ai.llm_model:
                    raise primary_error
                    
                logger.warning("No DB fallback models available. Engaging ultimate default fallback.")
                from syncsphere.ai.domain.entities.model import AIModel, ModelProvider
                fallback_provider = ModelProvider(id="ultimate_fallback_provider", org_id=org_id, name=settings.ai.llm_provider, api_key_encrypted="dummy_encrypted_key")
                fallback_model = AIModel(id="ultimate_fallback_model", org_id=org_id, provider_id=fallback_provider.id, name=settings.ai.llm_model, display_name="System Default (Fallback)", capabilities=[])
                providers_dict[fallback_provider.id] = fallback_provider
                
            fallback_provider = providers_dict.get(fallback_model.provider_id)
            
            logger.warning(
                "AI Fallback | Provider selected: %s | Configured model: %s | Fallback model: %s | API key present: %s | Exact failure reason: %s",
                provider.name, model.name, fallback_model.name, bool(api_key), str(primary_error)
            )
            
            if not self.circuit_breaker.can_execute(fallback_provider.name):
                from syncsphere.ai.domain.exceptions import ModelNotFoundException
                raise ModelNotFoundException(fallback_model.name)
                
            fallback_adapter = self.provider_registry.get(fallback_provider.name)
            if not fallback_adapter:
                from syncsphere.ai.domain.exceptions import ModelNotFoundException
                raise ModelNotFoundException(fallback_model.name)
            
            fallback_key = self._decrypt_api_key(fallback_provider)
            try:
                result = await fallback_adapter.structured_output(
                    model_name=fallback_model.name,
                    messages=messages,
                    schema=schema,
                    settings=settings,
                    api_key=fallback_key,
                    api_url=fallback_provider.api_url_override
                )
                self.circuit_breaker.record_success(fallback_provider.name)
                return result
            except Exception as fallback_err:
                self.circuit_breaker.record_failure(fallback_provider.name)
                raise fallback_err
