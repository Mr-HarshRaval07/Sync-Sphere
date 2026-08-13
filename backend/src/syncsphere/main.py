from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from syncsphere.core.config.settings import settings
from syncsphere.core.lifecycle.lifespan import get_lifespan
from syncsphere.core.middleware import (
    CorrelationIdMiddleware,
    TenantMiddleware,
    register_error_handlers,
)
from syncsphere.core.logging import RequestLoggingMiddleware
from syncsphere.presentation.api import v1_router
from syncsphere.shared_kernel.infrastructure.logging.logger import get_logger
from syncsphere.core.scheduler import init_scheduler, shutdown_scheduler

logger = get_logger("syncsphere.main")

from syncsphere.identity.infrastructure.documents import (
    OrgDocument,
    RoleDocument,
    UserDocument,
    ApiKeyDocument,
    RefreshTokenDocument,
    DeveloperApiKeyDocument,
)
from syncsphere.connectors.infrastructure.documents import (
    ConnectorDocument,
    ConnectorCredentialDocument,
)
from syncsphere.workflow.infrastructure.documents import (
    WorkflowDocument,
    WorkflowVersionDocument,
    WorkflowTemplateDocument,
    WorkflowScheduleDocument,
)
from syncsphere.ai.infrastructure.documents import (
    AIModelDocument,
    ModelProviderDocument,
    PromptTemplateDocument,
    PromptVersionDocument,
    PromptExecutionDocument,
)
from syncsphere.planner.infrastructure.documents import (
    PlanningSessionDocument,
    PlannerTraceDocument,
)
from syncsphere.runtime.infrastructure.documents import (
    ExecutionSessionDocument,
    ExecutionTraceDocument,
)
from syncsphere.knowledge.infrastructure.documents import (
    KnowledgeSourceDocument,
    KnowledgeDocumentDocument,
    KnowledgeChunkDocument,
    SemanticCacheEntryDocument,
    MemoryDocument,
)
from syncsphere.approval.infrastructure.documents.approval_request_document import ApprovalRequestDocument
from syncsphere.approval.infrastructure.documents.approval_delegate_document import ApprovalDelegateDocument
from syncsphere.approval.infrastructure.documents.approval_policy_document import ApprovalPolicyDocument
from syncsphere.approval.infrastructure.documents.approval_template_document import ApprovalTemplateDocument

# Observability Documents
from syncsphere.observability.infrastructure.documents.trace_document import TraceDocument
from syncsphere.observability.infrastructure.documents.replay_document import (
    ExecutionReplayDocument,
    WorkflowReplayDocument,
    PlannerReplayDocument
)
from syncsphere.observability.infrastructure.documents.metric_document import MetricSeriesDocument
from syncsphere.observability.infrastructure.documents.alert_document import AlertDocument
from syncsphere.observability.infrastructure.documents.health_document import HealthCheckDocument
from syncsphere.observability.infrastructure.documents.log_document import StructuredLogDocument
from syncsphere.observability.infrastructure.documents.event_store_document import EventStoreEntryDocument

# Tasks Module Documents
from syncsphere.tasks.documents import (
    TaskDocument,
    SlackTokenDocument,
    OAuthStateDocument,
    GoogleTokenDocument,
    GitHubTokenDocument,
    JiraTokenDocument,
    NotionTokenDocument,
    AutomationWorkflowDocument,
    WorkflowExecutionLogDocument,
)

# Instantiate FastAPI Application with Modular Lifespan
app = FastAPI(
    title=settings.app.name,  # Access app config name
    description="SyncSphere AI - Multi-Agent Workflow Orchestration Platform API",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=get_lifespan([
        OrgDocument,
        RoleDocument,
        UserDocument,
        ApiKeyDocument,
        DeveloperApiKeyDocument,
        RefreshTokenDocument,
        ConnectorDocument,
        ConnectorCredentialDocument,
        WorkflowDocument,
        WorkflowVersionDocument,
        WorkflowTemplateDocument,
        WorkflowScheduleDocument,
        AIModelDocument,
        ModelProviderDocument,
        PromptTemplateDocument,
        PromptVersionDocument,
        PromptExecutionDocument,
        PlanningSessionDocument,
        PlannerTraceDocument,
        ExecutionSessionDocument,
        ExecutionTraceDocument,
        KnowledgeSourceDocument,
        KnowledgeDocumentDocument,
        KnowledgeChunkDocument,
        SemanticCacheEntryDocument,
        MemoryDocument,
        ApprovalRequestDocument,
        ApprovalDelegateDocument,
        ApprovalPolicyDocument,
        ApprovalTemplateDocument,
        TraceDocument,
        ExecutionReplayDocument,
        WorkflowReplayDocument,
        PlannerReplayDocument,
        MetricSeriesDocument,
        AlertDocument,
        HealthCheckDocument,
        StructuredLogDocument,
        EventStoreEntryDocument,
        TaskDocument,
        SlackTokenDocument,
        OAuthStateDocument,
        GoogleTokenDocument,
        GitHubTokenDocument,
        JiraTokenDocument,
        NotionTokenDocument,
        AutomationWorkflowDocument,
        WorkflowExecutionLogDocument,
    ]),
)

from syncsphere.core.config.app import Environment

# 1. Mount Global Middleware
origins = [settings.frontend_url]
if settings.app.environment == Environment.LOCAL:
    origins.extend([
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
        "http://localhost:3002",
        "http://127.0.0.1:3002",
        "http://localhost:8000",
        "http://127.0.0.1:8000"
    ])
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(TenantMiddleware)
app.add_middleware(CorrelationIdMiddleware)

# 2. Register Global Exception Handlers
register_error_handlers(app)

# 3. Mount Routers
app.include_router(v1_router)

@app.get("/health")
def health_check():
    return {"status": "ok", "app": settings.app.name, "environment": settings.app.environment.value}
