import asyncio
from typing import Generator, Any, AsyncGenerator
from unittest.mock import AsyncMock, MagicMock
from syncsphere.main import app
import pytest


# ============================================================
# TEST ENVIRONMENT
# ============================================================

from syncsphere.core.config.settings import settings
from syncsphere.core.config.app import Environment

settings.environment = Environment.TEST


# ============================================================
# MOCK AI PROVIDER
# ============================================================

from syncsphere.ai.domain.value_objects import (
    ChatResponse,
    CompletionResponse,
    StreamingChunk,
    StructuredOutputResult,
    TokenUsage,
    CostUsage,
)


class MockAIProvider:
    """
    Fully deterministic AI provider used only during tests.

    IMPORTANT:
    This provider must never make network calls.

    It implements all gateway operations used by the AI platform:
      - chat
      - completion
      - embeddings
      - streaming
      - structured output
    """

    async def generate_chat(
        self,
        model_name,
        messages,
        settings,
        api_key,
        api_url=None,
    ):
        return ChatResponse(
            message_content="Mock AI response",
            token_usage=TokenUsage(
                prompt_tokens=10,
                completion_tokens=5,
                total_tokens=15,
            ),
            cost_usage=CostUsage(
                prompt_cost=0.0,
                completion_cost=0.0,
                total_cost=0.0,
            ),
        )

    async def generate_completion(
        self,
        model_name,
        prompt,
        settings,
        api_key,
        api_url=None,
    ):
        return CompletionResponse(
            text="Mock completion response",
            token_usage=TokenUsage(
                prompt_tokens=10,
                completion_tokens=5,
                total_tokens=15,
            ),
            cost_usage=CostUsage(
                prompt_cost=0.0,
                completion_cost=0.0,
                total_cost=0.0,
            ),
        )

    async def generate_embedding(
        self,
        model_name,
        input_texts,
        api_key,
        api_url=None,
    ):
        """
        Deterministic 1536-dimensional embeddings.

        No external API call.
        """
        return [
            [0.0] * 1536
            for _ in input_texts
        ]

    async def stream_completion(
        self,
        model_name,
        prompt,
        settings,
        api_key,
        api_url=None,
    ) -> AsyncGenerator[StreamingChunk, None]:
        """
        Deterministic streaming implementation.

        Yields immediately and never waits on external services.
        """

        chunks = [
            "Mock ",
            "streaming ",
            "response",
        ]

        for text in chunks:
            yield StreamingChunk(
                delta_text=text
            )

    async def structured_output(
        self,
        model_name,
        messages,
        schema,
        settings,
        api_key,
        api_url=None,
    ):
        """
        Deterministic structured-output response.

        The exact parsed payload is intentionally minimal because
        the integration tests primarily verify routing and gateway
        behavior.
        """

        return StructuredOutputResult(
            success=True,
            raw_output="{}",
            error_message=None,
        )


# One shared deterministic provider instance.
MOCK_AI_PROVIDER = MockAIProvider()


# ============================================================
# MOCK DATABASE CONNECTION
# ============================================================

from syncsphere.shared_kernel.infrastructure.mongodb.connection import (
    mongodb_manager,
)

mongodb_manager.connect = AsyncMock()
mongodb_manager.disconnect = AsyncMock()
mongodb_manager.client = MagicMock()
mongodb_manager.db = MagicMock()


# ============================================================
# MOCK REDIS CONNECTION
# ============================================================

from syncsphere.shared_kernel.infrastructure.redis.connection import (
    redis_manager,
)


async def dummy_async(*args, **kwargs):
    """
    Generic async no-op used for mocked infrastructure calls.
    """
    return None


redis_manager.connect = AsyncMock()
redis_manager.disconnect = AsyncMock()
redis_manager.ping = AsyncMock(return_value=True)

redis_manager.client = MagicMock()


# ------------------------------------------------------------
# Redis Pub/Sub mock
# ------------------------------------------------------------

mock_pubsub = MagicMock()

mock_pubsub.psubscribe = AsyncMock()
mock_pubsub.punsubscribe = AsyncMock()

# Never connect to a real Redis server.
mock_pubsub.get_message = AsyncMock(return_value=None)

mock_pubsub.close = AsyncMock()

redis_manager.client.pubsub.return_value = mock_pubsub

redis_manager.client.publish = AsyncMock(return_value=None)


# ============================================================
# DEPENDENCY INJECTION CONTAINER
# ============================================================

from syncsphere.core.dependency_injection.container import container

from tests.mocks import (
    InMemoryUserRepository,
    InMemoryOrgRepository,
    InMemoryRoleRepository,
    InMemoryApiKeyRepository,
    InMemoryRefreshTokenRepository,
    InMemoryConnectorRepository,
    InMemoryCredentialRepository,
    InMemoryWorkflowRepository,
    InMemoryWorkflowVersionRepository,
    InMemoryAIModelRepository,
    InMemoryModelProviderRepository,
    InMemoryPromptTemplateRepository,
    InMemoryPromptVersionRepository,
    InMemoryPromptExecutionRepository,
    InMemoryPlanningSessionRepository,
    InMemoryPlannerTraceRepository,
    InMemoryPlannerPromptRepository,
)


# ============================================================
# EVENT LOOP
# ============================================================

@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """
    Session-scoped event loop for async tests.
    """

    loop = asyncio.new_event_loop()

    try:
        yield loop
    finally:
        loop.close()


# ============================================================
# CLEAN / RESET ALL TEST REPOSITORIES
# ============================================================

@pytest.fixture(autouse=True)
def clean_repositories():
    """
    Completely isolates every test.

    All repositories are in-memory.
    All external infrastructure is mocked.
    All AI requests use MockAIProvider.
    """

    # ========================================================
    # AUTH / USER
    # ========================================================

    container.user_repo = InMemoryUserRepository()
    container.org_repo = InMemoryOrgRepository()
    container.role_repo = InMemoryRoleRepository()
    container.api_key_repo = InMemoryApiKeyRepository()
    container.token_repo = InMemoryRefreshTokenRepository()

    container.connector_repo = InMemoryConnectorRepository()
    container.connector_credential_repo = InMemoryCredentialRepository()

    container.auth_service.user_repo = container.user_repo
    container.auth_service.org_repo = container.org_repo
    container.auth_service.role_repo = container.role_repo
    container.auth_service.api_key_repo = container.api_key_repo
    container.auth_service.token_repo = container.token_repo
    container.auth_service.event_bus = container.event_bus

    container.rbac_service.user_repo = container.user_repo
    container.rbac_service.role_repo = container.role_repo

    container.connector_service.connector_repo = container.connector_repo
    container.connector_service.credential_repo = (
        container.connector_credential_repo
    )

    # ========================================================
    # WORKFLOW
    # ========================================================

    container.workflow_repo = InMemoryWorkflowRepository()
    container.workflow_version_repo = InMemoryWorkflowVersionRepository()

    container.workflow_service.workflow_repo = container.workflow_repo
    container.workflow_service.version_repo = (
        container.workflow_version_repo
    )

    # ========================================================
    # AI REPOSITORIES
    # ========================================================

    container.model_repo = InMemoryAIModelRepository()
    container.model_provider_repo = InMemoryModelProviderRepository()

    container.prompt_template_repo = (
        InMemoryPromptTemplateRepository()
    )

    container.prompt_version_repo = (
        InMemoryPromptVersionRepository()
    )

    container.prompt_execution_repo = (
        InMemoryPromptExecutionRepository()
    )

    # ========================================================
    # EVENT BUS
    # ========================================================

    container.event_bus = MagicMock()

    container.event_bus.publish = AsyncMock(
        return_value=None
    )

    container.event_bus.subscribe = AsyncMock(
        return_value=None
    )

    # ========================================================
    # AI SERVICES
    # ========================================================

    container.ai_service.model_repo = container.model_repo
    container.ai_service.provider_repo = (
        container.model_provider_repo
    )
    container.ai_service.event_bus = container.event_bus

    container.prompt_service.template_repo = (
        container.prompt_template_repo
    )

    container.prompt_service.version_repo = (
        container.prompt_version_repo
    )

    container.prompt_service.event_bus = container.event_bus

    container.prompt_engine.template_repo = (
        container.prompt_template_repo
    )

    container.prompt_engine.version_repo = (
        container.prompt_version_repo
    )

    # ========================================================
    # AI GATEWAY
    # ========================================================

    container.ai_gateway.model_repo = container.model_repo

    container.ai_gateway.provider_repo = (
        container.model_provider_repo
    )

    container.ai_gateway.execution_repo = (
        container.prompt_execution_repo
    )

    container.ai_gateway.event_bus = container.event_bus

    # CRITICAL:
    # The integration test creates provider "mock".
    # Force that provider to the deterministic mock.
    container.ai_gateway.provider_registry = {
        "mock": MOCK_AI_PROVIDER
    }

    # ========================================================
    # DISABLE REAL AI GATEWAY INFRASTRUCTURE
    # ========================================================
    #
    # These components are intentionally deterministic during
    # tests. They must never introduce waits/network activity.
    #

    container.ai_gateway.rate_limiter = MagicMock()
    container.ai_gateway.rate_limiter.check_limits = MagicMock(
        return_value=None
    )

    container.ai_gateway.circuit_breaker = MagicMock()

    container.ai_gateway.circuit_breaker.can_execute = MagicMock(
        return_value=True
    )

    container.ai_gateway.circuit_breaker.record_success = MagicMock(
        return_value=None
    )

    container.ai_gateway.circuit_breaker.record_failure = MagicMock(
        return_value=None
    )

    container.ai_gateway.cache = MagicMock()

    # Always miss cache.
    container.ai_gateway.cache.get = MagicMock(
        return_value=None
    )

    container.ai_gateway.cache.set = MagicMock(
        return_value=None
    )

    # ========================================================
    # PLANNER
    # ========================================================

    container.planner_session_repo = (
        InMemoryPlanningSessionRepository()
    )

    container.planner_trace_repo = (
        InMemoryPlannerTraceRepository()
    )

    container.planner_prompt_repo = (
        InMemoryPlannerPromptRepository()
    )

    container.planner_service.session_repo = (
        container.planner_session_repo
    )

    container.planner_service.trace_repo = (
        container.planner_trace_repo
    )

    container.planner_service.event_bus = container.event_bus

    container.planner_service.connector_repo = (
        container.connector_repo
    )

    container.planner_service.model_repo = (
        container.model_repo
    )

    container.planner_service.workflow_repo = (
        container.workflow_repo
    )

    container.planner_service.version_repo = (
        container.workflow_version_repo
    )

    # ========================================================
    # PIPELINE REFERENCES
    # ========================================================

    container.connector_discovery_service.connector_repo = (
        container.connector_repo
    )

    container.tool_selector.discovery_service = (
        container.connector_discovery_service
    )

    # ========================================================
    # RUNTIME
    # ========================================================

    from tests.mocks import (
        InMemoryExecutionSessionRepository,
        InMemoryExecutionTraceRepository,
    )

    container.execution_session_repo = (
        InMemoryExecutionSessionRepository()
    )

    container.execution_trace_repo = (
        InMemoryExecutionTraceRepository()
    )

    from syncsphere.runtime.application.services.engine import (
        StepExecutor,
    )

    container.step_executor = StepExecutor(
        connector_service=container.connector_service
    )

    container.execution_engine.session_repo = (
        container.execution_session_repo
    )

    container.execution_engine.trace_repo = (
        container.execution_trace_repo
    )

    container.execution_engine.workflow_repo = (
        container.workflow_repo
    )

    container.execution_engine.version_repo = (
        container.workflow_version_repo
    )

    container.execution_engine.event_bus = (
        container.event_bus
    )

    container.execution_pipeline.session_repo = (
        container.execution_session_repo
    )

    container.execution_pipeline.trace_repo = (
        container.execution_trace_repo
    )

    container.execution_pipeline.workflow_repo = (
        container.workflow_repo
    )

    container.execution_pipeline.step_executor = (
        container.step_executor
    )

    container.execution_pipeline.event_bus = (
        container.event_bus
    )

    # ========================================================
    # KNOWLEDGE PLATFORM
    # ========================================================

    from tests.mocks import (
        InMemoryKnowledgeSourceRepository,
        InMemoryKnowledgeDocumentRepository,
        InMemoryKnowledgeChunkRepository,
        InMemorySemanticCacheRepository,
        InMemoryMemoryRepository,
    )

    container.knowledge_source_repo = (
        InMemoryKnowledgeSourceRepository()
    )

    container.knowledge_doc_repo = (
        InMemoryKnowledgeDocumentRepository()
    )

    container.knowledge_chunk_repo = (
        InMemoryKnowledgeChunkRepository()
    )

    container.semantic_cache_repo = (
        InMemorySemanticCacheRepository()
    )

    container.knowledge_memory_repo = (
        InMemoryMemoryRepository()
    )

    container.embedding_pipeline.ai_gateway = (
        container.ai_gateway
    )

    container.vector_store.chunk_repo = (
        container.knowledge_chunk_repo
    )

    container.knowledge_pipeline.source_repo = (
        container.knowledge_source_repo
    )

    container.knowledge_pipeline.document_repo = (
        container.knowledge_doc_repo
    )

    container.knowledge_pipeline.chunk_repo = (
        container.knowledge_chunk_repo
    )

    container.knowledge_pipeline.vector_store = (
        container.vector_store
    )

    container.knowledge_pipeline.embedding_pipeline = (
        container.embedding_pipeline
    )

    container.retrieval_pipeline.vector_store = (
        container.vector_store
    )

    container.retrieval_pipeline.embedding_pipeline = (
        container.embedding_pipeline
    )

    container.retrieval_pipeline.document_repo = (
        container.knowledge_doc_repo
    )

    container.semantic_cache_service.repo = (
        container.semantic_cache_repo
    )

    container.semantic_cache_service.embedding_pipeline = (
        container.embedding_pipeline
    )

    container.knowledge_memory_service.repo = (
        container.knowledge_memory_repo
    )

    container.connector_sync_service.source_repo = (
        container.knowledge_source_repo
    )

    container.connector_sync_service.connector_service = (
        container.connector_service
    )

    container.connector_sync_service.knowledge_pipeline = (
        container.knowledge_pipeline
    )

    container.knowledge_service.source_repo = (
        container.knowledge_source_repo
    )

    container.knowledge_service.document_repo = (
        container.knowledge_doc_repo
    )

    container.knowledge_service.chunk_repo = (
        container.knowledge_chunk_repo
    )

    container.knowledge_service.cache_repo = (
        container.semantic_cache_repo
    )

    container.knowledge_service.knowledge_pipeline = (
        container.knowledge_pipeline
    )

    container.knowledge_service.retrieval_pipeline = (
        container.retrieval_pipeline
    )

    container.knowledge_service.cache_service = (
        container.semantic_cache_service
    )

    container.knowledge_service.memory_service = (
        container.knowledge_memory_service
    )

    container.knowledge_service.sync_service = (
        container.connector_sync_service
    )

    container.knowledge_service.event_bus = (
        container.event_bus
    )

    # ========================================================
    # APPROVAL
    # ========================================================

    from tests.mocks import (
        InMemoryApprovalRequestRepository,
        InMemoryApprovalDelegateRepository,
        InMemoryApprovalPolicyRepository,
        InMemoryApprovalTemplateRepository,
    )

    container.approval_request_repo = (
        InMemoryApprovalRequestRepository()
    )

    container.approval_delegate_repo = (
        InMemoryApprovalDelegateRepository()
    )

    container.approval_policy_repo = (
        InMemoryApprovalPolicyRepository()
    )

    container.approval_template_repo = (
        InMemoryApprovalTemplateRepository()
    )

    container.approval_pipeline.request_repo = (
        container.approval_request_repo
    )

    container.approval_pipeline.policy_repo = (
        container.approval_policy_repo
    )

    container.approval_pipeline.template_repo = (
        container.approval_template_repo
    )

    container.approval_pipeline.delegate_repo = (
        container.approval_delegate_repo
    )

    container.approval_service.request_repo = (
        container.approval_request_repo
    )

    container.approval_service.delegate_repo = (
        container.approval_delegate_repo
    )

    container.approval_service.policy_repo = (
        container.approval_policy_repo
    )

    container.approval_service.template_repo = (
        container.approval_template_repo
    )

    container.approval_service.event_bus = (
        container.event_bus
    )

    container.approval_notifier.connector_repo = (
        container.connector_repo
    )

    container.approval_notifier.connector_service = (
        container.connector_service
    )

    container.approver_resolver.user_repo = (
        container.user_repo
    )

    container.approver_resolver.role_repo = (
        container.role_repo
    )

    # ========================================================
    # OBSERVABILITY
    # ========================================================

    from tests.mocks import (
        InMemoryTraceRepository,
        InMemoryReplayRepository,
        InMemoryMetricRepository,
        InMemoryAlertRepository,
        InMemoryHealthRepository,
        InMemoryLogRepository,
        InMemoryEventStoreRepository,
    )

    from syncsphere.observability.application.services.live_telemetry import (
        WebSocketHub,
        TelemetryBroadcaster,
    )

    from syncsphere.observability.application.services.event_store_service import (
        EventStoreService,
    )

    from syncsphere.observability.application.services.tracing import (
        DistributedTracer,
        TraceCollector,
    )

    from syncsphere.observability.application.services.metrics import (
        MetricsCollector,
    )

    from syncsphere.observability.application.services.logging import (
        StructuredLogger,
    )

    from syncsphere.observability.application.services.alerting import (
        AlertEngine,
    )

    from syncsphere.observability.application.services.health import (
        HealthAggregator,
        HealthReporter,
    )

    from syncsphere.observability.application.services.analytics import (
        AIAnalyticsEngine,
        ConnectorAnalyticsEngine,
        PlannerAnalytics,
        RuntimeAnalytics,
        KnowledgeAnalytics,
        ApprovalAnalytics,
        OrganizationAnalytics,
        UsageAnalytics,
        CostAnalytics,
    )

    from syncsphere.observability.application.services.replay import (
        ExecutionReplayEngine,
        WorkflowReplayEngine,
        PlannerReplayEngine,
    )

    from syncsphere.observability.application.pipelines import (
        LoggingPipeline,
        MetricsPipeline,
        TracingPipeline,
        ReplayPipeline,
        AlertPipeline,
        DashboardPipeline,
        TelemetryPipeline,
    )

    from syncsphere.observability.application.services.observability_service import (
        ObservabilityService,
    )

    container.observability_trace_repo = (
        InMemoryTraceRepository()
    )

    container.observability_replay_repo = (
        InMemoryReplayRepository()
    )

    container.observability_metric_repo = (
        InMemoryMetricRepository()
    )

    container.observability_alert_repo = (
        InMemoryAlertRepository()
    )

    container.observability_health_repo = (
        InMemoryHealthRepository()
    )

    container.observability_log_repo = (
        InMemoryLogRepository()
    )

    container.observability_event_store_repo = (
        InMemoryEventStoreRepository()
    )

    container.observability_websocket_hub = WebSocketHub()

    container.observability_broadcaster = TelemetryBroadcaster(
        container.observability_websocket_hub
    )

    container.observability_event_store_service = (
        EventStoreService(
            container.observability_event_store_repo
        )
    )

    container.observability_tracer = DistributedTracer(
        container.observability_trace_repo
    )

    container.observability_trace_collector = TraceCollector(
        container.observability_tracer
    )

    container.observability_metrics_collector = (
        MetricsCollector(
            container.observability_metric_repo
        )
    )

    container.observability_logger = StructuredLogger(
        container.observability_log_repo
    )

    container.observability_alert_engine = AlertEngine(
        container.observability_alert_repo
    )

    container.observability_health_aggregator = (
        HealthAggregator(
            container.observability_health_repo
        )
    )

    container.observability_health_reporter = (
        HealthReporter(
            container.observability_health_aggregator
        )
    )

    container.observability_ai_analytics = AIAnalyticsEngine(
        container.observability_metric_repo,
        container.observability_event_store_repo,
    )

    container.observability_conn_analytics = (
        ConnectorAnalyticsEngine(
            container.observability_metric_repo,
            container.observability_event_store_repo,
        )
    )

    container.observability_plan_analytics = (
        PlannerAnalytics(
            container.observability_event_store_repo
        )
    )

    container.observability_run_analytics = RuntimeAnalytics(
        container.observability_event_store_repo
    )

    container.observability_know_analytics = KnowledgeAnalytics(
        container.observability_event_store_repo
    )

    container.observability_appr_analytics = ApprovalAnalytics(
        container.observability_event_store_repo
    )

    container.observability_org_analytics = (
        OrganizationAnalytics(
            container.observability_ai_analytics,
            container.observability_conn_analytics,
        )
    )

    container.observability_use_analytics = UsageAnalytics(
        container.observability_run_analytics,
        container.observability_plan_analytics,
    )

    container.observability_cost_analytics = CostAnalytics(
        container.observability_ai_analytics
    )

    container.observability_exe_replay = (
        ExecutionReplayEngine(
            container.observability_replay_repo,
            container.observability_event_store_repo,
        )
    )

    container.observability_wf_replay = (
        WorkflowReplayEngine(
            container.observability_replay_repo,
            container.observability_event_store_repo,
        )
    )

    container.observability_pl_replay = (
        PlannerReplayEngine(
            container.observability_replay_repo,
            container.observability_event_store_repo,
        )
    )

    container.observability_logging_pipeline = LoggingPipeline(
        container.observability_logger
    )

    container.observability_metrics_pipeline = MetricsPipeline(
        container.observability_metrics_collector
    )

    container.observability_tracing_pipeline = TracingPipeline(
        container.observability_trace_collector
    )

    container.observability_replay_pipeline = ReplayPipeline(
        exe=container.observability_exe_replay,
        wf=container.observability_wf_replay,
        pl=container.observability_pl_replay,
    )

    container.observability_alert_pipeline = AlertPipeline(
        container.observability_alert_engine
    )

    container.observability_dashboard_pipeline = (
        DashboardPipeline(
            ai=container.observability_ai_analytics,
            conn=container.observability_conn_analytics,
            plan=container.observability_plan_analytics,
            run=container.observability_run_analytics,
            know=container.observability_know_analytics,
            appr=container.observability_appr_analytics,
            org=container.observability_org_analytics,
            use=container.observability_use_analytics,
            cost=container.observability_cost_analytics,
            health=container.observability_health_aggregator,
        )
    )

    container.observability_telemetry_pipeline = (
        TelemetryPipeline(
            logging=container.observability_logging_pipeline,
            metrics=container.observability_metrics_pipeline,
            tracing=container.observability_tracing_pipeline,
            alerts=container.observability_alert_pipeline,
            event_store=container.observability_event_store_service,
        )
    )

    container.observability_service = ObservabilityService(
        trace_repo=container.observability_trace_repo,
        alert_repo=container.observability_alert_repo,
        log_repo=container.observability_log_repo,
        health_repo=container.observability_health_repo,
        event_store_repo=container.observability_event_store_repo,
        telemetry_pipeline=container.observability_telemetry_pipeline,
        logging_pipeline=container.observability_logging_pipeline,
        metrics_pipeline=container.observability_metrics_pipeline,
        tracing_pipeline=container.observability_tracing_pipeline,
        replay_pipeline=container.observability_replay_pipeline,
        alert_pipeline=container.observability_alert_pipeline,
        dashboard_pipeline=container.observability_dashboard_pipeline,
        broadcaster=container.observability_broadcaster,
        event_publisher=container.event_bus,
    )

    # IMPORTANT:
    # Do not allow observability tests to use Redis cache.
    container.observability_metrics_collector.cache = None