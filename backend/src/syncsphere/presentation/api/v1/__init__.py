from fastapi import APIRouter
from .health import router as health_router
from syncsphere.connectors.presentation import (
    connector_router,
    oauth_router,
)
from syncsphere.identity.presentation import (
    auth_router,
    user_router,
    org_router,
    role_router,
)
from syncsphere.identity.presentation.routes.developer_key_routes import router as developer_key_router

from syncsphere.workflow.presentation import workflow_router, schedule_router
from syncsphere.ai.presentation import ai_router
from syncsphere.planner.presentation.routes import planner_router
from syncsphere.runtime.presentation import runtime_router
from syncsphere.knowledge.presentation import knowledge_router
from syncsphere.approval.presentation.routes.approval_routes import router as approval_router
from syncsphere.observability.presentation.routes.observability_routes import router as observability_router
from syncsphere.tasks.router import router as task_router
from syncsphere.tasks.automation_routes import router as automation_router
from syncsphere.connectors.presentation.webhook_routes import router as webhook_router

v1_router = APIRouter()
v1_router.include_router(health_router, prefix="/v1")
v1_router.include_router(auth_router, prefix="/v1")
v1_router.include_router(user_router, prefix="/v1")
v1_router.include_router(org_router, prefix="/v1")
v1_router.include_router(role_router, prefix="/v1")
v1_router.include_router(developer_key_router, prefix="/v1")
v1_router.include_router(connector_router, prefix="/v1")
v1_router.include_router(oauth_router, prefix="/v1")
v1_router.include_router(workflow_router, prefix="/v1")
v1_router.include_router(schedule_router, prefix="/v1")
v1_router.include_router(ai_router, prefix="/v1")
v1_router.include_router(planner_router, prefix="/v1")
v1_router.include_router(runtime_router, prefix="/v1")
v1_router.include_router(knowledge_router, prefix="/v1")
v1_router.include_router(approval_router, prefix="/v1")
v1_router.include_router(observability_router, prefix="/v1")
v1_router.include_router(task_router, prefix="/v1")
v1_router.include_router(automation_router, prefix="/v1")
v1_router.include_router(webhook_router, prefix="/v1")
from syncsphere.workflow.presentation.routes.global_schedule_routes import router as global_scheduler
v1_router.include_router(global_scheduler)

__all__ = ["v1_router"]
