import pytest
import asyncio
from typing import Generator, Any
from unittest.mock import AsyncMock, MagicMock

# Force settings to TEST environment for all test runs
from syncsphere.core.config.settings import settings
from syncsphere.core.config.app import Environment
settings.environment = Environment.TEST

# Mock connection managers before any tests run
from syncsphere.shared_kernel.infrastructure.mongodb.connection import mongodb_manager
from syncsphere.shared_kernel.infrastructure.redis.connection import redis_manager

mongodb_manager.connect = AsyncMock()
mongodb_manager.disconnect = AsyncMock()
mongodb_manager.client = MagicMock()
mongodb_manager.db = MagicMock()

async def dummy_async(*args, **kwargs):
    return None

redis_manager.connect = MagicMock()
redis_manager.disconnect = AsyncMock()
redis_manager.ping = AsyncMock(return_value=True)
redis_manager.client = MagicMock()
redis_manager.client.publish = dummy_async

# Inject InMemory Repositories into DI Container for testing
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

@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Creates a session-scoped event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(autouse=True)
def clean_repositories():
    """
    Cleans/reinitializes in-memory stubs before each test case
    to ensure perfect test isolation.
    """
    container.user_repo = InMemoryUserRepository()
    container.org_repo = InMemoryOrgRepository()
    container.role_repo = InMemoryRoleRepository()
    container.api_key_repo = InMemoryApiKeyRepository()
    container.token_repo = InMemoryRefreshTokenRepository()
    container.connector_repo = InMemoryConnectorRepository()
    container.connector_credential_repo = InMemoryCredentialRepository()
    
    # Re-wire services using the new stub repositories
    container.auth_service.user_repo = container.user_repo
    container.auth_service.org_repo = container.org_repo
    container.auth_service.role_repo = container.role_repo
    container.auth_service.api_key_repo = container.api_key_repo
    container.auth_service.token_repo = container.token_repo
    
    container.rbac_service.user_repo = container.user_repo
    container.rbac_service.role_repo = container.role_repo

    container.connector_service.connector_repo = container.connector_repo
    container.connector_service.credential_repo = container.connector_credential_repo

    # Workflow context
    container.workflow_repo = InMemoryWorkflowRepository()
    container.workflow_version_repo = InMemoryWorkflowVersionRepository()
    container.workflow_service.workflow_repo = container.workflow_repo
    container.workflow_service.version_repo = container.workflow_version_repo

    # AI context
    container.model_repo = InMemoryAIModelRepository()
    container.model_provider_repo = InMemoryModelProviderRepository()
    container.prompt_template_repo = InMemoryPromptTemplateRepository()
    container.prompt_version_repo = InMemoryPromptVersionRepository()
    container.prompt_execution_repo = InMemoryPromptExecutionRepository()

    # Mock Event Bus to prevent Redis hangs in test environment
    container.event_bus = MagicMock()
    container.event_bus.publish = dummy_async
    container.event_bus.subscribe = dummy_async

    container.ai_service.model_repo = container.model_repo
    container.ai_service.provider_repo = container.model_provider_repo
    container.ai_service.event_bus = container.event_bus

    container.prompt_service.template_repo = container.prompt_template_repo
    container.prompt_service.version_repo = container.prompt_version_repo
    container.prompt_service.event_bus = container.event_bus

    container.prompt_engine.template_repo = container.prompt_template_repo
    container.prompt_engine.version_repo = container.prompt_version_repo

    container.ai_gateway.model_repo = container.model_repo
    container.ai_gateway.provider_repo = container.model_provider_repo
    container.ai_gateway.execution_repo = container.prompt_execution_repo
    container.ai_gateway.event_bus = container.event_bus

    # Planner context resets
    container.planner_session_repo = InMemoryPlanningSessionRepository()
    container.planner_trace_repo = InMemoryPlannerTraceRepository()
    container.planner_prompt_repo = InMemoryPlannerPromptRepository()
    
    container.planner_service.session_repo = container.planner_session_repo
    container.planner_service.trace_repo = container.planner_trace_repo
    container.planner_service.event_bus = container.event_bus
    container.planner_service.connector_repo = container.connector_repo
    container.planner_service.model_repo = container.model_repo
    container.planner_service.workflow_repo = container.workflow_repo
    container.planner_service.version_repo = container.workflow_version_repo
    
    # Update pipeline references
    container.connector_discovery_service.connector_repo = container.connector_repo
    container.tool_selector.discovery_service = container.connector_discovery_service

    # Runtime context resets
    from tests.mocks import (
        InMemoryExecutionSessionRepository,
        InMemoryExecutionTraceRepository
    )
    container.execution_session_repo = InMemoryExecutionSessionRepository()
    container.execution_trace_repo = InMemoryExecutionTraceRepository()

    from syncsphere.runtime.application.services.engine import StepExecutor
    container.step_executor = StepExecutor(connector_service=container.connector_service)

    container.execution_engine.session_repo = container.execution_session_repo
    container.execution_engine.trace_repo = container.execution_trace_repo
    container.execution_engine.workflow_repo = container.workflow_repo
    container.execution_engine.version_repo = container.workflow_version_repo
    container.execution_engine.event_bus = container.event_bus

    container.execution_pipeline.session_repo = container.execution_session_repo
    container.execution_pipeline.trace_repo = container.execution_trace_repo
    container.execution_pipeline.workflow_repo = container.workflow_repo
    container.execution_pipeline.step_executor = container.step_executor
    container.execution_pipeline.event_bus = container.event_bus

    # Knowledge Platform context resets
    from tests.mocks import (
        InMemoryKnowledgeSourceRepository,
        InMemoryKnowledgeDocumentRepository,
        InMemoryKnowledgeChunkRepository,
        InMemorySemanticCacheRepository,
        InMemoryMemoryRepository
    )
    container.knowledge_source_repo = InMemoryKnowledgeSourceRepository()
    container.knowledge_doc_repo = InMemoryKnowledgeDocumentRepository()
    container.knowledge_chunk_repo = InMemoryKnowledgeChunkRepository()
    container.semantic_cache_repo = InMemorySemanticCacheRepository()
    container.knowledge_memory_repo = InMemoryMemoryRepository()

    container.embedding_pipeline.ai_gateway = container.ai_gateway
    container.vector_store.chunk_repo = container.knowledge_chunk_repo

    container.knowledge_pipeline.source_repo = container.knowledge_source_repo
    container.knowledge_pipeline.document_repo = container.knowledge_doc_repo
    container.knowledge_pipeline.chunk_repo = container.knowledge_chunk_repo
    container.knowledge_pipeline.vector_store = container.vector_store
    container.knowledge_pipeline.embedding_pipeline = container.embedding_pipeline

    container.retrieval_pipeline.vector_store = container.vector_store
    container.retrieval_pipeline.embedding_pipeline = container.embedding_pipeline
    container.retrieval_pipeline.document_repo = container.knowledge_doc_repo

    container.semantic_cache_service.repo = container.semantic_cache_repo
    container.semantic_cache_service.embedding_pipeline = container.embedding_pipeline

    container.knowledge_memory_service.repo = container.knowledge_memory_repo

    container.connector_sync_service.source_repo = container.knowledge_source_repo
    container.connector_sync_service.connector_service = container.connector_service
    container.connector_sync_service.knowledge_pipeline = container.knowledge_pipeline

    container.knowledge_service.source_repo = container.knowledge_source_repo
    container.knowledge_service.document_repo = container.knowledge_doc_repo
    container.knowledge_service.chunk_repo = container.knowledge_chunk_repo
    container.knowledge_service.cache_repo = container.semantic_cache_repo
    container.knowledge_service.knowledge_pipeline = container.knowledge_pipeline
    container.knowledge_service.retrieval_pipeline = container.retrieval_pipeline
    container.knowledge_service.cache_service = container.semantic_cache_service
    container.knowledge_service.memory_service = container.knowledge_memory_service
    container.knowledge_service.sync_service = container.connector_sync_service
    container.knowledge_service.event_bus = container.event_bus

    # Approval context resets
    from tests.mocks import (
        InMemoryApprovalRequestRepository,
        InMemoryApprovalDelegateRepository,
        InMemoryApprovalPolicyRepository,
        InMemoryApprovalTemplateRepository
    )
    container.approval_request_repo = InMemoryApprovalRequestRepository()
    container.approval_delegate_repo = InMemoryApprovalDelegateRepository()
    container.approval_policy_repo = InMemoryApprovalPolicyRepository()
    container.approval_template_repo = InMemoryApprovalTemplateRepository()

    container.approval_pipeline.request_repo = container.approval_request_repo
    container.approval_pipeline.policy_repo = container.approval_policy_repo
    container.approval_pipeline.template_repo = container.approval_template_repo
    container.approval_pipeline.delegate_repo = container.approval_delegate_repo

    container.approval_service.request_repo = container.approval_request_repo
    container.approval_service.delegate_repo = container.approval_delegate_repo
    container.approval_service.policy_repo = container.approval_policy_repo
    container.approval_service.template_repo = container.approval_template_repo
    container.approval_service.event_bus = container.event_bus

    # Fix dependency leaks to prevent real MongoDB collection queries
    container.approval_notifier.connector_repo = container.connector_repo
    container.approval_notifier.connector_service = container.connector_service
    container.approver_resolver.user_repo = container.user_repo
    container.approver_resolver.role_repo = container.role_repo

    # Observability context resets
    from tests.mocks import (
        InMemoryTraceRepository,
        InMemoryReplayRepository,
        InMemoryMetricRepository,
        InMemoryAlertRepository,
        InMemoryHealthRepository,
        InMemoryLogRepository,
        InMemoryEventStoreRepository
    )
    from syncsphere.observability.application.services.live_telemetry import WebSocketHub, TelemetryBroadcaster
    from syncsphere.observability.application.services.event_store_service import EventStoreService
    from syncsphere.observability.application.services.tracing import DistributedTracer, TraceCollector
    from syncsphere.observability.application.services.metrics import MetricsCollector
    from syncsphere.observability.application.services.logging import StructuredLogger
    from syncsphere.observability.application.services.alerting import AlertEngine
    from syncsphere.observability.application.services.health import HealthAggregator, HealthReporter
    from syncsphere.observability.application.services.analytics import (
        AIAnalyticsEngine,
        ConnectorAnalyticsEngine,
        PlannerAnalytics,
        RuntimeAnalytics,
        KnowledgeAnalytics,
        ApprovalAnalytics,
        OrganizationAnalytics,
        UsageAnalytics,
        CostAnalytics
    )
    from syncsphere.observability.application.services.replay import (
        ExecutionReplayEngine,
        WorkflowReplayEngine,
        PlannerReplayEngine
    )
    from syncsphere.observability.application.pipelines import (
        LoggingPipeline,
        MetricsPipeline,
        TracingPipeline,
        ReplayPipeline,
        AlertPipeline,
        DashboardPipeline,
        TelemetryPipeline
    )
    from syncsphere.observability.application.services.observability_service import ObservabilityService

    container.observability_trace_repo = InMemoryTraceRepository()
    container.observability_replay_repo = InMemoryReplayRepository()
    container.observability_metric_repo = InMemoryMetricRepository()
    container.observability_alert_repo = InMemoryAlertRepository()
    container.observability_health_repo = InMemoryHealthRepository()
    container.observability_log_repo = InMemoryLogRepository()
    container.observability_event_store_repo = InMemoryEventStoreRepository()

    container.observability_websocket_hub = WebSocketHub()
    container.observability_broadcaster = TelemetryBroadcaster(container.observability_websocket_hub)
    container.observability_event_store_service = EventStoreService(container.observability_event_store_repo)
    
    container.observability_tracer = DistributedTracer(container.observability_trace_repo)
    container.observability_trace_collector = TraceCollector(container.observability_tracer)
    container.observability_metrics_collector = MetricsCollector(container.observability_metric_repo)
    container.observability_logger = StructuredLogger(container.observability_log_repo)
    container.observability_alert_engine = AlertEngine(container.observability_alert_repo)
    container.observability_health_aggregator = HealthAggregator(container.observability_health_repo)
    container.observability_health_reporter = HealthReporter(container.observability_health_aggregator)

    container.observability_ai_analytics = AIAnalyticsEngine(container.observability_metric_repo, container.observability_event_store_repo)
    container.observability_conn_analytics = ConnectorAnalyticsEngine(container.observability_metric_repo, container.observability_event_store_repo)
    container.observability_plan_analytics = PlannerAnalytics(container.observability_event_store_repo)
    container.observability_run_analytics = RuntimeAnalytics(container.observability_event_store_repo)
    container.observability_know_analytics = KnowledgeAnalytics(container.observability_event_store_repo)
    container.observability_appr_analytics = ApprovalAnalytics(container.observability_event_store_repo)
    
    container.observability_org_analytics = OrganizationAnalytics(container.observability_ai_analytics, container.observability_conn_analytics)
    container.observability_use_analytics = UsageAnalytics(container.observability_run_analytics, container.observability_plan_analytics)
    container.observability_cost_analytics = CostAnalytics(container.observability_ai_analytics)

    container.observability_exe_replay = ExecutionReplayEngine(container.observability_replay_repo, container.observability_event_store_repo)
    container.observability_wf_replay = WorkflowReplayEngine(container.observability_replay_repo, container.observability_event_store_repo)
    container.observability_pl_replay = PlannerReplayEngine(container.observability_replay_repo, container.observability_event_store_repo)

    container.observability_logging_pipeline = LoggingPipeline(container.observability_logger)
    container.observability_metrics_pipeline = MetricsPipeline(container.observability_metrics_collector)
    container.observability_tracing_pipeline = TracingPipeline(container.observability_trace_collector)
    
    container.observability_replay_pipeline = ReplayPipeline(
        exe=container.observability_exe_replay,
        wf=container.observability_wf_replay,
        pl=container.observability_pl_replay
    )
    container.observability_alert_pipeline = AlertPipeline(container.observability_alert_engine)
    
    container.observability_dashboard_pipeline = DashboardPipeline(
        ai=container.observability_ai_analytics,
        conn=container.observability_conn_analytics,
        plan=container.observability_plan_analytics,
        run=container.observability_run_analytics,
        know=container.observability_know_analytics,
        appr=container.observability_appr_analytics,
        org=container.observability_org_analytics,
        use=container.observability_use_analytics,
        cost=container.observability_cost_analytics,
        health=container.observability_health_aggregator
    )

    container.observability_telemetry_pipeline = TelemetryPipeline(
        logging=container.observability_logging_pipeline,
        metrics=container.observability_metrics_pipeline,
        tracing=container.observability_tracing_pipeline,
        alerts=container.observability_alert_pipeline,
        event_store=container.observability_event_store_service
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
        event_publisher=container.event_bus
    )

    # Disable Redis caching during tests
    container.observability_metrics_collector.cache = None




