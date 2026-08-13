import logging
from typing import Optional

from syncsphere.core.config.settings import settings, Settings
from syncsphere.shared_kernel.infrastructure.mongodb.connection import (
    mongodb_manager,
    MongoDBConnectionManager,
)
from syncsphere.shared_kernel.infrastructure.redis.connection import (
    redis_manager,
    RedisConnectionManager,
)
from syncsphere.core.events.registry import EventRegistry
from syncsphere.core.events.redis_bus import RedisEventBus


# Identity Context imports
from syncsphere.identity.infrastructure.repositories import (
    MongoUserRepository,
    MongoOrgRepository,
    MongoRoleRepository,
    MongoApiKeyRepository,
    MongoRefreshTokenRepository,
)
from syncsphere.identity.infrastructure.hashing import PasswordHasherService
from syncsphere.identity.infrastructure.jwt_service import JWTService
from syncsphere.identity.infrastructure.token_generator import TokenGeneratorService
from syncsphere.identity.application.services.auth_service import AuthApplicationService
from syncsphere.identity.application.services.rbac_service import RBACApplicationService


logger = logging.getLogger(
    "syncsphere.core.dependency_injection.container"
)


class AppContainer:
    """
    Composition Root for SyncSphere.

    Maintains, wires, and injects infrastructure
    and application singletons.
    """

    def __init__(self) -> None:

        self.settings: Settings = settings

        self.mongodb: MongoDBConnectionManager = mongodb_manager

        self.redis: RedisConnectionManager = redis_manager

        # ============================================================
        # Core Events Infrastructure
        # ============================================================

        self.event_registry: EventRegistry = EventRegistry()

        self.event_bus: Optional[RedisEventBus] = None

        # ============================================================
        # Identity Domain Repositories
        # ============================================================

        self.user_repo = MongoUserRepository()

        self.org_repo = MongoOrgRepository()

        self.role_repo = MongoRoleRepository()

        self.api_key_repo = MongoApiKeyRepository()

        self.token_repo = MongoRefreshTokenRepository()

        # ============================================================
        # Identity Cryptography & Token Utilities
        # ============================================================

        self.hasher = PasswordHasherService()

        self.jwt_service = JWTService()

        self.token_gen = TokenGeneratorService()

        # ============================================================
        # Identity Application Services
        # ============================================================

        self.auth_service = AuthApplicationService(
            user_repo=self.user_repo,
            org_repo=self.org_repo,
            role_repo=self.role_repo,
            api_key_repo=self.api_key_repo,
            token_repo=self.token_repo,
            hasher=self.hasher,
            jwt_service=self.jwt_service,
            token_gen=self.token_gen,
        )

        self.rbac_service = RBACApplicationService(
            user_repo=self.user_repo,
            role_repo=self.role_repo,
        )

        # ============================================================
        # Connector Context Imports & Registrations
        # ============================================================

        from syncsphere.connectors.infrastructure.repositories import (
            MongoConnectorRepository,
            MongoCredentialRepository,
        )

        from syncsphere.connectors.infrastructure.loader import (
            ConnectorLoader,
        )

        from syncsphere.connectors.infrastructure.encryption import (
            FernetSecretProvider,
        )

        from syncsphere.connectors.application.services.connector_service import (
            ConnectorApplicationService,
        )

        self.secret_provider = FernetSecretProvider()

        self.connector_repo = MongoConnectorRepository()

        self.connector_credential_repo = MongoCredentialRepository()

        self.connector_loader = ConnectorLoader()

        self.connector_service = ConnectorApplicationService(
            connector_repo=self.connector_repo,
            credential_repo=self.connector_credential_repo,
            loader=self.connector_loader,
            secret_provider=self.secret_provider,
        )

        # ============================================================
        # Workflow Context Imports & Registrations
        # ============================================================

        from syncsphere.workflow.infrastructure.repositories import (
            MongoWorkflowRepository,
            MongoWorkflowVersionRepository,
        )

        from syncsphere.workflow.application.services.workflow_service import (
            WorkflowApplicationService,
        )

        self.workflow_repo = MongoWorkflowRepository()

        self.workflow_version_repo = MongoWorkflowVersionRepository()

        self.workflow_service = WorkflowApplicationService(
            workflow_repo=self.workflow_repo,
            version_repo=self.workflow_version_repo,
        )

        # ============================================================
        # AI Platform Context Imports & Registrations
        # ============================================================

        from syncsphere.ai.infrastructure.repositories import (
            MongoAIModelRepository,
            MongoModelProviderRepository,
            MongoPromptTemplateRepository,
            MongoPromptVersionRepository,
            MongoPromptExecutionRepository,
        )

        from syncsphere.ai.infrastructure.providers import (
            OpenAIProviderAdapter,
            AnthropicProviderAdapter,
            GeminiProviderAdapter,
            OllamaProviderAdapter,
            MockAIProvider,
        )

        # OpenRouter Provider Adapter
        from syncsphere.ai.infrastructure.providers.openrouter import (
            OpenRouterProviderAdapter,
        )

        from syncsphere.ai.application.services.ai_service import (
            AIService,
        )

        from syncsphere.ai.application.services.prompt_service import (
            PromptService,
        )

        from syncsphere.ai.application.services.prompt_engine import (
            PromptEngine,
        )

        from syncsphere.ai.application.services.ai_gateway_impl import (
            AIGatewayImpl,
        )

        from syncsphere.ai.infrastructure.engine.circuit_breaker import (
            CircuitBreaker,
        )

        from syncsphere.ai.infrastructure.engine.rate_limiter import (
            TenantRateLimiter,
        )

        from syncsphere.ai.infrastructure.engine.cache import (
            InferenceCache,
        )

        # ============================================================
        # AI Repositories
        # ============================================================

        self.model_repo = MongoAIModelRepository()

        self.model_provider_repo = MongoModelProviderRepository()

        self.prompt_template_repo = MongoPromptTemplateRepository()

        self.prompt_version_repo = MongoPromptVersionRepository()

        self.prompt_execution_repo = MongoPromptExecutionRepository()

        # ============================================================
        # AI Application Services
        # ============================================================

        self.ai_service = AIService(
            model_repo=self.model_repo,
            provider_repo=self.model_provider_repo,
            event_bus=self.event_bus,
        )

        self.prompt_service = PromptService(
            template_repo=self.prompt_template_repo,
            version_repo=self.prompt_version_repo,
            event_bus=self.event_bus,
        )

        self.prompt_engine = PromptEngine(
            template_repo=self.prompt_template_repo,
            version_repo=self.prompt_version_repo,
        )

        # ============================================================
        # Provider Adapters
        # ============================================================

        self.openai_adapter = OpenAIProviderAdapter()

        self.anthropic_adapter = AnthropicProviderAdapter()

        # Existing Gemini provider.
        # Keep this available for embeddings and future fallback use.
        self.gemini_adapter = GeminiProviderAdapter()

        self.ollama_adapter = OllamaProviderAdapter()

        self.mock_adapter = MockAIProvider()

        # OpenRouter provider.
        # This will be used when provider = "openrouter".
        self.openrouter_adapter = OpenRouterProviderAdapter()

        # ============================================================
        # Provider Registry
        # ============================================================

        provider_registry = {
            "openai": self.openai_adapter,

            "anthropic": self.anthropic_adapter,

            "gemini": self.gemini_adapter,

            "openrouter": self.openrouter_adapter,

            "ollama": self.ollama_adapter,

            "mock": self.mock_adapter,
        }

        logger.info(
            "AI provider registry initialized: %s",
            list(provider_registry.keys()),
        )

        # ============================================================
        # AI Infrastructure Engines
        # ============================================================

        self.circuit_breaker = CircuitBreaker()

        self.rate_limiter = TenantRateLimiter()

        self.inference_cache = InferenceCache()

        # ============================================================
        # AI Gateway
        # ============================================================

        self.ai_gateway = AIGatewayImpl(
            model_repo=self.model_repo,
            provider_repo=self.model_provider_repo,
            execution_repo=self.prompt_execution_repo,
            secret_provider=self.secret_provider,
            event_bus=self.event_bus,
            provider_registry=provider_registry,
            circuit_breaker=self.circuit_breaker,
            rate_limiter=self.rate_limiter,
            cache=self.inference_cache,
        )

        # ============================================================
        # Planner Bounded Context
        # ============================================================

        from syncsphere.planner.infrastructure.repositories import (
            MongoPlanningSessionRepository,
            MongoPlannerTraceRepository,
            MongoPlannerPromptRepository,
        )

        from syncsphere.planner.domain.services.intent import (
            IntentClassifier,
            EntityExtractor,
            GoalExtractor,
            ConstraintExtractor,
        )

        from syncsphere.planner.domain.services.validator import (
            WorkflowValidator,
        )

        from syncsphere.planner.domain.services.reasoning import (
            TaskDecomposer,
            PlannerReflectionEngine,
            ReasoningEngine,
        )

        from syncsphere.planner.domain.services.connector_intel import (
            ConnectorDiscoveryService,
            ToolSelector,
        )

        from syncsphere.planner.domain.strategies import (
            SimplePlanningStrategy,
            ReasoningPlanningStrategy,
            ReflectionPlanningStrategy,
            TreeOfThoughtPlanningStrategy,
        )

        from syncsphere.planner.domain.pipeline import (
            DefaultPlanningPipeline,
        )

        from syncsphere.planner.application.services.planner_service import (
            PlannerApplicationService,
        )

        from syncsphere.planner.infrastructure.prompts.library import (
            SYSTEM_DECOMPOSITION_PROMPT,
            SYSTEM_REFLECTION_PROMPT,
        )

        self.planner_session_repo = MongoPlanningSessionRepository()

        self.planner_trace_repo = MongoPlannerTraceRepository()

        self.planner_prompt_repo = MongoPlannerPromptRepository(
            {
                "decomposition": SYSTEM_DECOMPOSITION_PROMPT,
                "reflection": SYSTEM_REFLECTION_PROMPT,
            }
        )

        self.intent_classifier = IntentClassifier(
            ai_gateway=self.ai_gateway
        )

        self.entity_extractor = EntityExtractor(
            ai_gateway=self.ai_gateway
        )

        self.goal_extractor = GoalExtractor(
            ai_gateway=self.ai_gateway
        )

        self.constraint_extractor = ConstraintExtractor(
            ai_gateway=self.ai_gateway
        )

        self.planner_validator = WorkflowValidator()

        self.task_decomposer = TaskDecomposer(
            ai_gateway=self.ai_gateway
        )

        self.planner_reflection_engine = PlannerReflectionEngine(
            ai_gateway=self.ai_gateway
        )

        self.reasoning_engine = ReasoningEngine(
            decomposer=self.task_decomposer,
            reflection_engine=self.planner_reflection_engine,
        )

        self.connector_discovery_service = ConnectorDiscoveryService(
            connector_repo=self.connector_repo
        )

        self.tool_selector = ToolSelector(
            discovery_service=self.connector_discovery_service
        )

        strategies = {
            "simple": SimplePlanningStrategy(
                reasoning_engine=self.reasoning_engine,
                tool_selector=self.tool_selector,
            ),
            "reasoning": ReasoningPlanningStrategy(
                reasoning_engine=self.reasoning_engine,
                tool_selector=self.tool_selector,
            ),
            "reflection": ReflectionPlanningStrategy(
                reasoning_engine=self.reasoning_engine,
                tool_selector=self.tool_selector,
                reflection_engine=self.planner_reflection_engine,
            ),
            "tree_of_thought": TreeOfThoughtPlanningStrategy(
                reasoning_engine=self.reasoning_engine,
                tool_selector=self.tool_selector,
            ),
        }

        self.planner_pipeline = DefaultPlanningPipeline(
            intent_classifier=self.intent_classifier,
            entity_extractor=self.entity_extractor,
            goal_extractor=self.goal_extractor,
            constraint_extractor=self.constraint_extractor,
            strategies=strategies,
            validator=self.planner_validator,
        )

        self.planner_service = PlannerApplicationService(
            session_repo=self.planner_session_repo,
            trace_repo=self.planner_trace_repo,
            pipeline=self.planner_pipeline,
            connector_repo=self.connector_repo,
            model_repo=self.model_repo,
            workflow_repo=self.workflow_repo,
            version_repo=self.workflow_version_repo,
            event_bus=self.event_bus,
        )

        # ============================================================
        # Runtime Bounded Context Registrations
        # ============================================================

        from syncsphere.runtime.infrastructure.repositories import (
            MongoExecutionSessionRepository,
            MongoExecutionTraceRepository,
        )

        from syncsphere.runtime.application.services.engine import (
            ExecutionEngine,
            StepExecutor,
        )

        from syncsphere.runtime.application.services.resource import (
            ResourceManager,
        )

        from syncsphere.runtime.application.strategies.worker import (
            LocalWorkerStrategy,
            AsyncWorkerStrategy,
            FutureDistributedWorkerStrategy,
            ExecutionDispatcher,
        )

        from syncsphere.runtime.application.pipeline.default import (
            DefaultExecutionPipeline,
        )

        self.execution_session_repo = MongoExecutionSessionRepository()

        self.execution_trace_repo = MongoExecutionTraceRepository()

        self.resource_manager = ResourceManager()

        self.step_executor = StepExecutor(
            connector_service=self.connector_service
        )

        local_worker = LocalWorkerStrategy()

        async_worker = AsyncWorkerStrategy()

        dist_worker = FutureDistributedWorkerStrategy()

        self.execution_dispatcher = ExecutionDispatcher(
            local_strategy=local_worker,
            async_strategy=async_worker,
            distributed_strategy=dist_worker,
        )

        self.execution_pipeline = DefaultExecutionPipeline(
            session_repo=self.execution_session_repo,
            trace_repo=self.execution_trace_repo,
            workflow_repo=self.workflow_repo,
            dispatcher=self.execution_dispatcher,
            step_executor=self.step_executor,
            event_bus=self.event_bus,
        )

        self.execution_engine = ExecutionEngine(
            session_repo=self.execution_session_repo,
            trace_repo=self.execution_trace_repo,
            workflow_repo=self.workflow_repo,
            version_repo=self.workflow_version_repo,
            resource_manager=self.resource_manager,
            pipeline=self.execution_pipeline,
            event_bus=self.event_bus,
        )

        # ============================================================
        # Knowledge Context Imports & Registrations
        # ============================================================

        from syncsphere.knowledge.infrastructure.repositories import (
            MongoKnowledgeSourceRepository,
            MongoKnowledgeDocumentRepository,
            MongoKnowledgeChunkRepository,
            MongoSemanticCacheRepository,
            MongoMemoryRepository,
        )

        from syncsphere.knowledge.application.services.embedding import (
            EmbeddingPipeline,
            EmbeddingCache,
        )

        from syncsphere.knowledge.application.services.vector import (
            MongoDBVectorStore,
        )

        from syncsphere.knowledge.application.pipeline.knowledge import (
            KnowledgePipeline,
        )

        from syncsphere.knowledge.application.pipeline.retrieval import (
            RetrievalPipeline,
        )

        from syncsphere.knowledge.application.services.cache import (
            SemanticCacheService,
        )

        from syncsphere.knowledge.application.services.memory import (
            MemoryService,
        )

        from syncsphere.knowledge.application.services.sync import (
            ConnectorSyncService,
        )

        from syncsphere.knowledge.application.services.knowledge_service import (
            KnowledgeApplicationService,
        )

        self.knowledge_source_repo = MongoKnowledgeSourceRepository()

        self.knowledge_doc_repo = MongoKnowledgeDocumentRepository()

        self.knowledge_chunk_repo = MongoKnowledgeChunkRepository()

        self.semantic_cache_repo = MongoSemanticCacheRepository()

        self.knowledge_memory_repo = MongoMemoryRepository()

        self.embedding_cache = EmbeddingCache()

        self.embedding_pipeline = EmbeddingPipeline(
            ai_gateway=self.ai_gateway,
            cache=self.embedding_cache,
        )

        self.vector_store = MongoDBVectorStore(
            chunk_repo=self.knowledge_chunk_repo
        )

        self.knowledge_pipeline = KnowledgePipeline(
            source_repo=self.knowledge_source_repo,
            document_repo=self.knowledge_doc_repo,
            chunk_repo=self.knowledge_chunk_repo,
            vector_store=self.vector_store,
            embedding_pipeline=self.embedding_pipeline,
        )

        self.retrieval_pipeline = RetrievalPipeline(
            vector_store=self.vector_store,
            embedding_pipeline=self.embedding_pipeline,
            document_repo=self.knowledge_doc_repo,
        )

        self.semantic_cache_service = SemanticCacheService(
            repo=self.semantic_cache_repo,
            embedding_pipeline=self.embedding_pipeline,
        )

        self.knowledge_memory_service = MemoryService(
            repo=self.knowledge_memory_repo
        )

        self.connector_sync_service = ConnectorSyncService(
            source_repo=self.knowledge_source_repo,
            connector_service=self.connector_service,
            knowledge_pipeline=self.knowledge_pipeline,
        )

        self.knowledge_service = KnowledgeApplicationService(
            source_repo=self.knowledge_source_repo,
            document_repo=self.knowledge_doc_repo,
            chunk_repo=self.knowledge_chunk_repo,
            cache_repo=self.semantic_cache_repo,
            knowledge_pipeline=self.knowledge_pipeline,
            retrieval_pipeline=self.retrieval_pipeline,
            cache_service=self.semantic_cache_service,
            memory_service=self.knowledge_memory_service,
            sync_service=self.connector_sync_service,
            event_bus=self.event_bus,
        )

        # ============================================================
        # Approval Context Imports & Registrations
        # ============================================================

        from syncsphere.approval.infrastructure.repositories.mongo_approval_request_repository import (
            MongoApprovalRequestRepository,
        )

        from syncsphere.approval.infrastructure.repositories.mongo_approval_delegate_repository import (
            MongoApprovalDelegateRepository,
        )

        from syncsphere.approval.infrastructure.repositories.mongo_approval_policy_repository import (
            MongoApprovalPolicyRepository,
        )

        from syncsphere.approval.infrastructure.repositories.mongo_approval_template_repository import (
            MongoApprovalTemplateRepository,
        )

        from syncsphere.approval.application.services.assignment import (
            ApproverResolver,
        )

        from syncsphere.approval.application.services.notification import (
            NotificationService,
        )

        from syncsphere.approval.application.pipeline import (
            ApprovalPipeline,
        )

        from syncsphere.approval.application.services.approval_service import (
            ApprovalApplicationService,
        )

        self.approval_request_repo = MongoApprovalRequestRepository()

        self.approval_delegate_repo = MongoApprovalDelegateRepository()

        self.approval_policy_repo = MongoApprovalPolicyRepository()

        self.approval_template_repo = MongoApprovalTemplateRepository()

        self.approver_resolver = ApproverResolver()

        self.approval_notifier = NotificationService(
            connector_repo=self.connector_repo,
            connector_service=self.connector_service,
        )

        self.approval_pipeline = ApprovalPipeline(
            request_repo=self.approval_request_repo,
            policy_repo=self.approval_policy_repo,
            template_repo=self.approval_template_repo,
            delegate_repo=self.approval_delegate_repo,
            approver_resolver=self.approver_resolver,
            notification_service=self.approval_notifier,
        )

        self.approval_service = ApprovalApplicationService(
            request_repo=self.approval_request_repo,
            delegate_repo=self.approval_delegate_repo,
            policy_repo=self.approval_policy_repo,
            template_repo=self.approval_template_repo,
            pipeline=self.approval_pipeline,
            event_bus=self.event_bus,
        )

        # ============================================================
        # Observability Context Imports & Registrations
        # ============================================================

        from syncsphere.observability.infrastructure.repositories import (
            MongoTraceRepository,
            MongoReplayRepository,
            MongoMetricRepository,
            MongoAlertRepository,
            MongoHealthRepository,
            MongoLogRepository,
            MongoEventStoreRepository,
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

        self.observability_trace_repo = MongoTraceRepository()

        self.observability_replay_repo = MongoReplayRepository()

        self.observability_metric_repo = MongoMetricRepository()

        self.observability_alert_repo = MongoAlertRepository()

        self.observability_health_repo = MongoHealthRepository()

        self.observability_log_repo = MongoLogRepository()

        self.observability_event_store_repo = MongoEventStoreRepository()

        self.observability_websocket_hub = WebSocketHub()

        self.observability_broadcaster = TelemetryBroadcaster(
            self.observability_websocket_hub
        )

        self.observability_event_store_service = EventStoreService(
            self.observability_event_store_repo
        )

        self.observability_tracer = DistributedTracer(
            self.observability_trace_repo
        )

        self.observability_trace_collector = TraceCollector(
            self.observability_tracer
        )

        self.observability_metrics_collector = MetricsCollector(
            self.observability_metric_repo
        )

        self.observability_logger = StructuredLogger(
            self.observability_log_repo
        )

        self.observability_alert_engine = AlertEngine(
            self.observability_alert_repo
        )

        self.observability_health_aggregator = HealthAggregator(
            self.observability_health_repo
        )

        self.observability_health_reporter = HealthReporter(
            self.observability_health_aggregator
        )

        self.observability_ai_analytics = AIAnalyticsEngine(
            self.observability_metric_repo,
            self.observability_event_store_repo,
        )

        self.observability_conn_analytics = ConnectorAnalyticsEngine(
            self.observability_metric_repo,
            self.observability_event_store_repo,
        )

        self.observability_plan_analytics = PlannerAnalytics(
            self.observability_event_store_repo
        )

        self.observability_run_analytics = RuntimeAnalytics(
            self.observability_event_store_repo
        )

        self.observability_know_analytics = KnowledgeAnalytics(
            self.observability_event_store_repo
        )

        self.observability_appr_analytics = ApprovalAnalytics(
            self.observability_event_store_repo
        )

        self.observability_org_analytics = OrganizationAnalytics(
            self.observability_ai_analytics,
            self.observability_conn_analytics,
        )

        self.observability_use_analytics = UsageAnalytics(
            self.observability_run_analytics,
            self.observability_plan_analytics,
        )

        self.observability_cost_analytics = CostAnalytics(
            self.observability_ai_analytics
        )

        self.observability_exe_replay = ExecutionReplayEngine(
            self.observability_replay_repo,
            self.observability_event_store_repo,
        )

        self.observability_wf_replay = WorkflowReplayEngine(
            self.observability_replay_repo,
            self.observability_event_store_repo,
        )

        self.observability_pl_replay = PlannerReplayEngine(
            self.observability_replay_repo,
            self.observability_event_store_repo,
        )

        self.observability_logging_pipeline = LoggingPipeline(
            self.observability_logger
        )

        self.observability_metrics_pipeline = MetricsPipeline(
            self.observability_metrics_collector
        )

        self.observability_tracing_pipeline = TracingPipeline(
            self.observability_trace_collector
        )

        self.observability_replay_pipeline = ReplayPipeline(
            exe=self.observability_exe_replay,
            wf=self.observability_wf_replay,
            pl=self.observability_pl_replay,
        )

        self.observability_alert_pipeline = AlertPipeline(
            self.observability_alert_engine
        )

        self.observability_dashboard_pipeline = DashboardPipeline(
            ai=self.observability_ai_analytics,
            conn=self.observability_conn_analytics,
            plan=self.observability_plan_analytics,
            run=self.observability_run_analytics,
            know=self.observability_know_analytics,
            appr=self.observability_appr_analytics,
            org=self.observability_org_analytics,
            use=self.observability_use_analytics,
            cost=self.observability_cost_analytics,
            health=self.observability_health_aggregator,
        )

        self.observability_telemetry_pipeline = TelemetryPipeline(
            logging=self.observability_logging_pipeline,
            metrics=self.observability_metrics_pipeline,
            tracing=self.observability_tracing_pipeline,
            alerts=self.observability_alert_pipeline,
            event_store=self.observability_event_store_service,
        )

        self.observability_service = ObservabilityService(
            trace_repo=self.observability_trace_repo,
            alert_repo=self.observability_alert_repo,
            log_repo=self.observability_log_repo,
            health_repo=self.observability_health_repo,
            event_store_repo=self.observability_event_store_repo,
            telemetry_pipeline=self.observability_telemetry_pipeline,
            logging_pipeline=self.observability_logging_pipeline,
            metrics_pipeline=self.observability_metrics_pipeline,
            tracing_pipeline=self.observability_tracing_pipeline,
            replay_pipeline=self.observability_replay_pipeline,
            alert_pipeline=self.observability_alert_pipeline,
            dashboard_pipeline=self.observability_dashboard_pipeline,
            broadcaster=self.observability_broadcaster,
            event_publisher=self.event_bus,
        )

        # ============================================================
        # Approval Completion Event Handler
        # ============================================================

        async def handle_approval_completed(event) -> None:

            from syncsphere.approval.domain.events import (
                ApprovalCompleted,
            )

            try:

                app_completed = ApprovalCompleted.model_validate(
                    event.model_dump()
                )

                if (
                    app_completed.session_id
                    and app_completed.node_id
                ):

                    logger.info(
                        "Event-driven resume triggered: "
                        "session %s node %s approved=%s",
                        app_completed.session_id,
                        app_completed.node_id,
                        app_completed.approved,
                    )

                    from syncsphere.runtime.application.commands import (
                        ApproveExecutionCommand,
                    )

                    cmd = ApproveExecutionCommand(
                        org_id=app_completed.org_id,
                        session_id=app_completed.session_id,
                        node_id=app_completed.node_id,
                        approved=app_completed.approved,
                        correlation_id=app_completed.correlation_id,
                    )

                    await self.execution_engine.approve_execution(
                        cmd
                    )

            except Exception as e:

                logger.error(
                    "Error in handle_approval_completed subscriber: %s",
                    e,
                )

        self.event_registry.register(
            "approval.completed",
            handle_approval_completed,
        )

        # ============================================================
        # Generic Telemetry Receiver
        # ============================================================

        async def handle_generic_telemetry(event) -> None:

            try:

                await self.observability_telemetry_pipeline.ingest_telemetry_event(
                    event_id=event.event_id,
                    event_type=event.event_type,
                    org_id=event.org_id,
                    correlation_id=event.correlation_id or "N/A",
                    timestamp=event.timestamp,
                    payload=event.model_dump(),
                )

            except Exception as e:

                logger.error(
                    "Failed to process telemetry event: %s",
                    e,
                )

        # ============================================================
        # Telemetry Event Types
        # ============================================================

        telemetry_event_types = [
            "auth.login",
            "auth.register",
            "connector.registered",
            "connector.enabled",
            "connector.disabled",
            "connector.handshake",
            "connector.tool_called",
            "connector.tool_failed",
            "workflow.created",
            "workflow.updated",
            "workflow.deleted",
            "workflow.published",
            "ai.completion_generated",
            "ai.embedding_generated",
            "ai.provider_healthy",
            "ai.provider_unhealthy",
            "ai.cache_hit",
            "ai.cache_miss",
            "planner.started",
            "planner.completed",
            "planner.rejected",
            "runtime.execution_started",
            "runtime.execution_completed",
            "runtime.execution_failed",
            "runtime.execution_paused",
            "runtime.execution_resumed",
            "knowledge.imported",
            "knowledge.indexed",
            "knowledge.search_executed",
            "approval.created",
            "approval.requested",
            "approval.completed",
            "approval.approved",
            "approval.rejected",
        ]

        for et in telemetry_event_types:

            self.event_registry.register(
                et,
                handle_generic_telemetry,
            )

    def wire_dependencies(self) -> None:
        """
        Wires up event bus once connection clients are online.
        """

        logger.info(
            "Wiring container dependency graph..."
        )

        if self.redis.client:

            self.event_bus = RedisEventBus(
                redis_client=self.redis.client,
                registry=self.event_registry,
            )

            logger.info(
                "RedisEventBus wired successfully in container."
            )

            # ========================================================
            # Wire AI Services Event Bus
            # ========================================================

            self.ai_service.event_bus = self.event_bus

            self.prompt_service.event_bus = self.event_bus

            self.ai_gateway.event_bus = self.event_bus

            self.planner_service.event_bus = self.event_bus

            self.execution_engine.event_bus = self.event_bus

            self.execution_pipeline.event_bus = self.event_bus

            self.knowledge_service.event_bus = self.event_bus

            self.approval_service.event_bus = self.event_bus

            self.observability_service.event_publisher = (
                self.event_bus
            )

            # ========================================================
            # Wire Redis Metrics Cache
            # ========================================================

            from syncsphere.observability.infrastructure.redis_cache import (
                RedisMetricCache,
            )

            self.observability_metrics_collector.cache = (
                RedisMetricCache(self.redis.client)
            )

        else:

            logger.warning(
                "Redis client unavailable; EventBus cannot be wired."
            )


# ================================================================
# Singleton Container Instance
# ================================================================

container = AppContainer()