import pytest
import asyncio
from typing import Dict, Any

from syncsphere.ai.domain.value_objects import (
    PromptVariable,
    ModelCapability,
    ModelSelectionPolicy,
    InferenceSettings,
    ModelHealth,
    ModelStatus,
    ProviderPriority,
)
from syncsphere.ai.domain.entities.model import AIModel, ModelProvider
from syncsphere.ai.domain.exceptions import (
    PromptCompilationException,
    InferenceQuotaExceededException,
)
from syncsphere.ai.application.services.prompt_engine import PromptEngine
from syncsphere.ai.application.services.policies import (
    FastPolicy,
    CheapPolicy,
    ReasoningPolicy,
    VisionPolicy,
    EmbeddingPolicy,
    ToolCallingPolicy,
)
from syncsphere.ai.infrastructure.engine.circuit_breaker import CircuitBreaker
from syncsphere.ai.infrastructure.engine.rate_limiter import TenantRateLimiter
from syncsphere.ai.infrastructure.engine.cache import InferenceCache
from syncsphere.ai.infrastructure.engine.token_counter import TokenCounter
from syncsphere.ai.infrastructure.engine.cost_calculator import CostCalculator
from tests.mocks import (
    InMemoryPromptTemplateRepository,
    InMemoryPromptVersionRepository,
)


@pytest.mark.asyncio
async def test_prompt_engine_compilation_and_rendering():
    template_repo = InMemoryPromptTemplateRepository()
    version_repo = InMemoryPromptVersionRepository()
    engine = PromptEngine(template_repo, version_repo)

    # 1. Create a prompt template with required & optional variables
    from syncsphere.ai.domain.entities.prompt import PromptTemplate
    template = PromptTemplate(
        org_id="org-123",
        name="test_prompt",
        description="A test prompt",
        variables=[
            PromptVariable(name="user_name", required=True),
            PromptVariable(name="action", required=False, default_val="login"),
            PromptVariable(name="nested_val", required=False)
        ]
    )
    await template_repo.save(template)

    # Save version
    version = template.create_version(
        system_template="System info for {{user_name}}.",
        user_template="Perform action: {{action}}. Details: {{nested_val}}.",
        description="Version 1"
    )
    await version_repo.save(version)
    await template_repo.save(template)

    # Compile with missing required variable should fail
    result_fail = await engine.compile("org-123", "test_prompt", {"action": "logout"})
    assert result_fail.is_fail
    assert isinstance(result_fail.error(), PromptCompilationException)

    # Compile with correct variables (supporting nested replacement)
    variables = {
        "user_name": "Bob",
        "nested_val": "Concept: {{dynamic_concept}}",
        "dynamic_concept": "recursion"
    }
    result_ok = await engine.compile("org-123", "test_prompt", variables)
    assert result_ok.is_ok
    data = result_ok.value()
    assert data["system"] == "System info for Bob."
    # The nested variable value containing placeholder should render recursively
    assert data["user"] == "Perform action: login. Details: Concept: recursion."


@pytest.mark.asyncio
async def test_prompt_engine_template_inheritance():
    template_repo = InMemoryPromptTemplateRepository()
    version_repo = InMemoryPromptVersionRepository()
    engine = PromptEngine(template_repo, version_repo)

    from syncsphere.ai.domain.entities.prompt import PromptTemplate
    template = PromptTemplate(
        org_id="org-123",
        name="test_prompt",
        variables=[]
    )
    await template_repo.save(template)

    # V1 (Parent)
    v1 = template.create_version(
        system_template="Base system prompt.",
        user_template="Base user prompt.",
        description="V1"
    )
    await version_repo.save(v1)

    # V2 (Child)
    v2 = template.create_version(
        system_template="Extended system prompt.",
        user_template="Extended user prompt.",
        description="V2"
    )
    v2.parent_version_id = v1.id
    await version_repo.save(v2)
    await template_repo.save(template)

    result = await engine.compile("org-123", "test_prompt", {}, version_num=2)
    assert result.is_ok
    data = result.value()
    # Expecting merged lines: parent prepended to child
    assert "Base system prompt." in data["system"]
    assert "Extended system prompt." in data["system"]


def test_circuit_breaker():
    breaker = CircuitBreaker(failure_threshold=2, cooldown_seconds=0.1)

    assert breaker.can_execute("openai")

    breaker.record_failure("openai")
    assert breaker.can_execute("openai") # threshold not hit yet

    breaker.record_failure("openai")
    assert not breaker.can_execute("openai") # OPEN

    # Wait for cooldown
    import time
    time.sleep(0.12)
    assert breaker.can_execute("openai") # Transitioned to HALF-OPEN

    # Success resets breaker
    breaker.record_success("openai")
    assert breaker.can_execute("openai")
    breaker.record_failure("openai")
    assert breaker.can_execute("openai") # needs 2 failures again


def test_rate_limiter():
    limiter = TenantRateLimiter(default_rpm=2, default_tpm=1000)

    # First request
    limiter.check_limits("org-123", estimated_tokens=400)
    # Second request
    limiter.check_limits("org-123", estimated_tokens=400)

    # Third request within 60s should fail RPM
    with pytest.raises(InferenceQuotaExceededException) as exc_info:
        limiter.check_limits("org-123", estimated_tokens=100)
    assert "inference usage quota exceeded" in str(exc_info.value)

    # Reset limiter for token test
    limiter_tpm = TenantRateLimiter(default_rpm=10, default_tpm=500)
    limiter_tpm.check_limits("org-456", estimated_tokens=400)
    with pytest.raises(InferenceQuotaExceededException) as exc_info_tpm:
        limiter_tpm.check_limits("org-456", estimated_tokens=200)
    assert "inference usage quota exceeded" in str(exc_info_tpm.value)


def test_inference_cache():
    cache = InferenceCache(default_ttl_seconds=0.05)

    prompt = "Hello"
    settings = InferenceSettings(temperature=0.7)
    cache.set(prompt, settings, "Cached Response")

    assert cache.get(prompt, settings) == "Cached Response"

    # Different settings should miss cache
    assert cache.get(prompt, InferenceSettings(temperature=0.2)) is None

    # Wait for TTL expiration
    import time
    time.sleep(0.06)
    assert cache.get(prompt, settings) is None


def test_token_and_cost_calculator():
    text = "Explain clean architecture in software development."
    tokens = TokenCounter.estimate_text_tokens(text, "gpt-4")
    assert tokens > 0

    # Pricing calculations
    model = AIModel(
        org_id="org-123",
        provider_id="prov-1",
        name="test-model",
        display_name="Test Model",
        capabilities=[ModelCapability.TEXT_GENERATION],
        cost_per_1k_input=0.001,
        cost_per_1k_output=0.002
    )

    cost = CostCalculator.calculate_cost(model, prompt_tokens=1000, completion_tokens=2000)
    assert cost.prompt_cost == 0.001
    assert cost.completion_cost == 0.004
    assert cost.total_cost == 0.005


def test_model_selection_policies():
    provider_1 = ModelProvider(
        org_id="org-123",
        name="openai",
        api_key_encrypted="enc-key",
        priority=ProviderPriority(priority_level=1),
        health=ModelHealth(is_healthy=True, latency_ms=100.0)
    )
    provider_2 = ModelProvider(
        org_id="org-123",
        name="anthropic",
        api_key_encrypted="enc-key",
        priority=ProviderPriority(priority_level=2),
        health=ModelHealth(is_healthy=True, latency_ms=50.0)
    )
    providers = {provider_1.id: provider_1, provider_2.id: provider_2}

    model_slow = AIModel(
        org_id="org-123",
        provider_id=provider_1.id,
        name="gpt-slow",
        display_name="GPT Slow",
        capabilities=[ModelCapability.TEXT_GENERATION],
        cost_per_1k_input=0.001,
        cost_per_1k_output=0.002
    )
    model_fast = AIModel(
        org_id="org-123",
        provider_id=provider_2.id,
        name="claude-fast",
        display_name="Claude Fast",
        capabilities=[ModelCapability.TEXT_GENERATION],
        cost_per_1k_input=0.005,
        cost_per_1k_output=0.01
    )
    models = [model_slow, model_fast]

    # Fast Policy resolves model with lowest provider latency (claude-fast: 50ms vs gpt-slow: 100ms)
    fast_sel = FastPolicy().select(models, providers)
    assert fast_sel.name == "claude-fast"

    # Cheap Policy resolves model with lowest total cost (gpt-slow: 0.003 vs claude-fast: 0.015)
    cheap_sel = CheapPolicy().select(models, providers)
    assert cheap_sel.name == "gpt-slow"
