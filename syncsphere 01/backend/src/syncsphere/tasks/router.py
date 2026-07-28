import asyncio
import logging
from typing import List, Optional, Literal
from datetime import datetime

import httpx
from beanie import PydanticObjectId
from fastapi import APIRouter, Request, Depends, HTTPException, status, BackgroundTasks

from syncsphere.shared_kernel.infrastructure.http.dependencies import verify_jwt
from syncsphere.shared_kernel.infrastructure.http.responses import ResponseEnvelope, ResponseMeta

from syncsphere.tasks.documents import TaskDocument, SlackTokenDocument
from syncsphere.tasks.schemas import CreateTaskRequest, UpdateTaskRequest, TaskResponse

from syncsphere.core.config.settings import settings


logger = logging.getLogger("syncsphere.tasks.router")

router = APIRouter(prefix="/tasks", tags=["Tasks"])

@router.get("/debug-models", status_code=200)
async def debug_models(request: Request, claims: dict = Depends(verify_jwt)):
    org_id = claims["org"]
    from syncsphere.core.dependency_injection.container import container
    models = await container.model_repo.list_by_org(org_id)
    providers = await container.model_provider_repo.list_by_org(org_id)
    return {
        "org_id": org_id,
        "models": [{"id": m.id, "name": m.name, "status": m.status, "caps": [c for c in m.capabilities]} for m in models],
        "providers": [{"id": p.id, "name": p.name} for p in providers]
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _doc_to_response(doc: TaskDocument) -> TaskResponse:
    from syncsphere.tasks.schemas import TaskAutomationSchema
    automation_schemas = []
    for auto in doc.automations:
        automation_schemas.append(
            TaskAutomationSchema(
                action=auto.action,
                config=auto.config,
                status=auto.status,
                error=auto.error,
                executed_at=auto.executed_at,
                result=auto.result,
            )
        )

    return TaskResponse(
        id=str(doc.id),
        org_id=doc.org_id,
        title=doc.title,
        description=doc.description,
        assigned_to=doc.assigned_to,
        priority=doc.priority,
        status=doc.status,
        due_date=doc.due_date,
        automations=automation_schemas,
        created_at=doc.created_at,
        updated_at=doc.updated_at,
    )


# ---------------------------------------------------------------------------
# Background: fire task.created automation workflows
# ---------------------------------------------------------------------------

async def _fire_task_created_workflows(
    doc: TaskDocument,
) -> None:
    """
    Fire the task.created trigger for all matching active automation workflows.
    Runs in background — does NOT block the task creation response.
    """
    try:
        from syncsphere.workflow.application.workflow_executor import fire_trigger

        trigger_data = {
            "task_id": str(doc.id),
            "title": doc.title,
            "description": doc.description,
            "assigned_to": doc.assigned_to,
            "priority": doc.priority,
            "status": doc.status,
            "due_date": doc.due_date or "Not set",
            # Pre-built message templates for convenience
            "slack_message": (
                f"📌 *New Task Created*\n\n"
                f"*Title:* {doc.title}\n"
                f"*Assigned To:* {doc.assigned_to or '-'}\n"
                f"*Priority:* {doc.priority}\n"
                f"*Status:* {doc.status}\n"
                f"*Due:* {doc.due_date or 'Not set'}\n\n"
                f"Created from SyncSphere 🚀"
            ),
            "email_subject": f"New Task: {doc.title}",
            "email_body": (
                f"A new task has been created in SyncSphere.\n\n"
                f"Title: {doc.title}\n"
                f"Description: {doc.description or '-'}\n"
                f"Assigned To: {doc.assigned_to or '-'}\n"
                f"Priority: {doc.priority}\n"
                f"Status: {doc.status}\n"
                f"Due Date: {doc.due_date or 'Not set'}\n"
            ),
        }

        await fire_trigger(
            trigger_app="task",
            trigger_event="task.created",
            trigger_data=trigger_data,
            organization_id=doc.org_id,
        )

    except Exception as exc:
        logger.warning(
            "task.created trigger failed for task %s: %s",
            doc.id,
            exc,
        )


# ---------------------------------------------------------------------------
# Legacy Slack helper (kept for backward compat if no automation workflow set up)
# ---------------------------------------------------------------------------

async def _post_slack_message_legacy(task: TaskDocument) -> None:
    """
    Legacy direct Slack notification — used only if no automation workflow
    matches task.created. Kept for backward compatibility.
    """
    from syncsphere.connectors.presentation.slack_actions import send_slack_message

    # Try to get channel from settings or use a default
    channel = getattr(settings, "slack_default_channel", None)
    if not channel:
        logger.info("No Slack default channel configured — skipping legacy Slack message")
        return

    try:
        message = (
            f"📌 *New Task Created*\n\n"
            f"*Title:* {task.title}\n"
            f"*Assigned To:* {task.assigned_to or '-'}\n"
            f"*Priority:* {task.priority}\n"
            f"*Status:* {task.status}\n"
            f"*Due:* {task.due_date or 'Not set'}\n\n"
            f"Created from SyncSphere 🚀"
        )
        await send_slack_message(channel=channel, message=message)
    except Exception as exc:
        logger.warning("Legacy Slack notification failed: %s", exc)


# ---------------------------------------------------------------------------
# POST /v1/tasks — Create task
# ---------------------------------------------------------------------------

@router.post(
    "",
    response_model=ResponseEnvelope[TaskResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create a new task",
)
async def create_task(
    request: Request,
    body: CreateTaskRequest,
    background_tasks: BackgroundTasks,
    claims: dict = Depends(verify_jwt),
) -> dict:
    correlation_id = getattr(request.state, "correlation_id", None)
    org_id = claims["org"]

    automations = []
    if body.automations:
        from syncsphere.tasks.documents import TaskAutomation
        automations = [
            TaskAutomation(action=a.action, config=a.config, status="pending") 
            for a in body.automations
        ]

    doc = TaskDocument(
        org_id=org_id,
        title=body.title,
        description=body.description,
        assigned_to=body.assigned_to,
        priority=body.priority,
        status=body.status,
        due_date=body.due_date,
        automations=automations,
    )
    await doc.insert()

    if doc.automations:
        asyncio.create_task(_execute_task_automation(doc))
    else:
        asyncio.create_task(_fire_task_created_workflows(doc))
        asyncio.create_task(_post_slack_message_legacy(doc))

    return {
        "data": _doc_to_response(doc),
        "meta": ResponseMeta(request_id=correlation_id),
    }


# ---------------------------------------------------------------------------
# AI Project Manager Endpoints (Phases 18–20)
# ---------------------------------------------------------------------------

from pydantic import BaseModel, Field
from syncsphere.ai.domain.value_objects import StructuredOutputSchema, ModelSelectionPolicy
from syncsphere.core.dependency_injection.container import container
from syncsphere.tasks.schemas import PlanWithAIRequest, ConfirmPlanRequest

class AIPlannedIntegration(BaseModel):
    action: str = Field(..., description="Action ID matching the ACTION_REGISTRY, e.g. gmail.send_email")
    selected: bool = Field(default=True, description="Whether this integration should be recommended by default")
    config: dict = Field(default_factory=dict, description="Extracted parameters explicitly generated from Prompt")
    missing_required_fields: List[str] = Field(default_factory=list, description="Fields required by this integration that could not be inferred")
    clarification_question: Optional[str] = Field(default=None, description="If required fields are missing for this integration, ask a direct question")

class AIPlannedTask(BaseModel):
    title: str = Field(..., description="User friendly title of the task")
    description: str = Field(..., description="Short description")
    assignee: str = Field(default="")
    assignee_email: Optional[str] = Field(default="", description="Assignee email if provided")
    priority: Literal["High", "Medium", "Low"] = Field(default="Medium")
    status: Literal["Pending", "In Progress", "Completed"] = Field(default="Pending")
    due_date: Optional[str] = None

class AIPlannedTaskSchema(BaseModel):
    task: AIPlannedTask
    integrations: List[AIPlannedIntegration] = Field(default_factory=list, description="Recommended automations")


@router.post(
    "/plan-with-ai",
    status_code=status.HTTP_200_OK,
    summary="Decompose a project goal into manual and automated tasks using AI",
)
async def plan_with_ai(
    request: Request,
    body: PlanWithAIRequest,
    claims: dict = Depends(verify_jwt),
) -> dict:
    import uuid
    from datetime import datetime, timezone

    correlation_id = getattr(request.state, "correlation_id", None) or str(uuid.uuid4())
    org_id = claims["org"]

    # ----- Structured request log (NEVER log the API key) -----
    logger.info(
        "plan-with-ai request started",
        extra={
            "request_id": correlation_id,
            "org_id": org_id,
            "model": None,        # resolved below
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "retry_count": 0,
        }
    )

    schema = StructuredOutputSchema(
        schema_name="AIPlannedTaskSchema",
        json_schema=AIPlannedTaskSchema.model_json_schema()
    )

    from syncsphere.tasks.documents import GoogleTokenDocument, SlackTokenDocument, GitHubTokenDocument
    has_google = await GoogleTokenDocument.find_one({"organization_id": org_id}) is not None
    has_slack = await SlackTokenDocument.find_one({"organization_id": org_id}) is not None
    has_github = await GitHubTokenDocument.find_one({"organization_id": org_id}) is not None

    connection_status_str = (
        f"- Google (Gmail/Calendar/Sheets): {'Connected' if has_google else 'Not connected'}\n"
        f"- Slack: {'Connected' if has_slack else 'Not connected'}\n"
        f"- GitHub: {'Connected' if has_github else 'Not connected'}\n"
    )

    from syncsphere.workflow.application.action_registry import CAPABILITY_REGISTRY

    actions_info = []
    for app_name, app_info in CAPABILITY_REGISTRY.items():
        for action_name, action_info in app_info["actions"].items():
            action_id = f"{app_name}.{action_name}"
            config_str = ", ".join([f"'{k}': {v['description']}" for k, v in action_info["input_schema"].items()])
            req_str = ", ".join(action_info.get("required_fields", []))
            actions_info.append(f"  - '{action_id}': {action_info['description']}\n    Required: [{req_str}]\n    Schema: {{{config_str}}}")

    actions_list_str = "\n".join(actions_info)

    messages = [
        {
            "role": "system",
            "content": (
                "You are an AI Project Manager for SyncSphere executing a ZERO-FRICTION experience. "
                "Extract the primary task details and AUTOMATICALLY configure the requested integrations in a SINGLE task object.\n\n"
                "## AVAILABLE INTEGRATIONS\n"
                f"{actions_list_str}\n\n"
                "## CONNECTION STATUS\n"
                f"{connection_status_str}\n\n"
                "## RULES\n"
                "1. DO NOT make the user manually fill in every field. Aggressively extract and generate parameters directly from the user's natural-language prompt whenever reasonably possible.\n"
                "2. For Slack, automatically generate the 'message'. For GitHub, automatically generate 'title' and 'body'. For Gmail, automatically generate 'subject' and 'body' if you understand the intent.\n"
                "3. ONLY add elements to 'missing_fields' if the information is critically missing (like a recipient email address, calendar ID, a Slack channel, or GitHub repository).\n"
                "4. CRITICAL: DO NOT INVENT PLACEHOLDER OR FAKE DATA. For example, never output '#general' for a Slack channel or 'your_email@domain.com' unless the user explicitly requested it. If missing, leave it out of the config dict and append the field name to 'missing_fields'.\n"
                "5. Automatically recommend the best integrations based only on intent. Do not blindly add all of them. ONLY select integrations that are explicitly available in the AVAILABLE INTEGRATIONS list.\n"
                "6. VERY IMPORTANT: You must output a JSON object with exactly these top-level keys: 'task', 'integrations', 'missing_fields', 'clarification_question'. Do NOT output 'project_name' or 'task_decomposition'.\n"
                "7. The 'task' top-level key MUST be an OBJECT containing exactly these: 'title', 'description', 'assignee', 'assignee_email', 'priority', 'status', 'due_date'.\n"
                "8. For each integration in 'integrations', you MUST use exactly the keys 'action', 'selected', and 'config'. Do NOT use 'provider' or 'type'. The 'action' string must PERFECTLY match one of the action keys in the list."
            )
        },
        {
            "role": "user",
            "content": body.prompt
        }
    ]

    result = await container.ai_gateway.structured_output(
        org_id=org_id,
        messages=messages,
        schema=schema,
        policy=ModelSelectionPolicy.FAST
    )

    if not result.success:
        err_msg = (result.error_message or "").lower()
        http_status = "unknown"
        if "429" in err_msg or "quota" in err_msg or "resource_exhausted" in err_msg:
            http_status = "429"
        elif "404" in err_msg:
            http_status = "404"
        elif "401" in err_msg or "403" in err_msg or "unauthorized" in err_msg:
            http_status = "401/403"
        elif "400" in err_msg:
            http_status = "400"
        else:
            http_status = "500"

        logger.warning(
            "plan-with-ai provider request failed",
            extra={
                "request_id": correlation_id,
                "org_id": org_id,
                "provider": result.provider_name or "unknown",
                "model": result.model_name or "unknown",
                "http_status": http_status,
                "retry_count": 0,
                "error_body": result.error_message or "",
            }
        )

        if http_status == "404":
            raise HTTPException(
                status_code=502,
                detail="Configured AI provider or model is unavailable."
            )
        elif http_status == "429":
            # Pass the actual provider name dynamically back to the frontend
            provider_name_display = result.provider_name.title() if result.provider_name else "AI"
            raise HTTPException(
                status_code=429,
                detail=f"{provider_name_display} API rate limit or quota exceeded. Please try again later."
            )
        elif http_status == "401/403":
            if "401" in err_msg:
                raise HTTPException(
                    status_code=502,
                    detail="AI provider authentication failed. Check your API key."
                )
            else:
                raise HTTPException(
                    status_code=502,
                    detail="AI provider permission or billing access denied."
                )
        elif http_status == "400":
            raise HTTPException(
                status_code=502,
                detail="AI provider rejected the request due to malformed payload."
            )
    
        raise HTTPException(
            status_code=502,
            detail="AI service is temporarily unavailable."
        )
    import json
    try:
        parsed = json.loads(result.raw_output)
        # Validate using Pydantic schema
        validated_data = AIPlannedTaskSchema(**parsed).model_dump()
        logger.info(
            "plan-with-ai request succeeded",
            extra={
                "request_id": correlation_id,
                "org_id": org_id,
                "provider": result.provider_name or "unknown",
                "model": result.model_name or "unknown",
                "http_status": "200",
                "retry_count": 0,
            }
        )
    except json.JSONDecodeError as exc:
        logger.error("plan-with-ai failed to parse JSON output", exc_info=True)
        raise HTTPException(status_code=502, detail="AI Provider returned an invalid response format.")
    except Exception as exc:
        import traceback
        logger.error(
            "plan-with-ai failed to validate Pydantic output",
            extra={
                "request_id": correlation_id,
                "org_id": org_id,
                "provider": result.provider_name or "unknown",
                "model": result.model_name or "unknown",
                "http_status": "200",
                "retry_count": 0,
            }
        )
        logger.debug("AI raw output: %s\n%s", exc, traceback.format_exc())
        raise HTTPException(status_code=502, detail="AI Provider returned a response that does not match the required plan schema.")

    return {
        "data": validated_data,
        "meta": ResponseMeta(request_id=correlation_id),
    }


@router.post(
    "/confirm-plan",
    response_model=ResponseEnvelope[List[TaskResponse]],
    status_code=status.HTTP_201_CREATED,
    summary="Create a bulk of tasks generated from the AI planner",
)
async def confirm_plan(
    request: Request,
    body: ConfirmPlanRequest,
    background_tasks: BackgroundTasks,
    claims: dict = Depends(verify_jwt),
) -> dict:
    correlation_id = getattr(request.state, "correlation_id", None)
    org_id = claims["org"]

    # Pre-flight Check: Ensure all required OAuth credentials exist
    from syncsphere.tasks.documents import GoogleTokenDocument, SlackTokenDocument, GitHubTokenDocument
    required_providers = set()
    
    for task_req in body.tasks:
        if task_req.automations:
            for auto in task_req.automations:
                prefix = auto.action.split(".")[0]
                if prefix in ["gmail", "google_calendar", "google_sheets", "google"]:
                    required_providers.add("google")
                elif prefix == "slack":
                    required_providers.add("slack")
                elif prefix == "github":
                    required_providers.add("github")

    missing_providers = []
    if "google" in required_providers:
        if not await GoogleTokenDocument.find_one({"organization_id": org_id}):
            missing_providers.append("google")
            
    print("========== PREFLIGHT DIAGNOSTIC ==========")
    print(f"Preflight tracking for org_id: {org_id!r}")
    
    if "slack" in required_providers:
        slack_token = await SlackTokenDocument.find_one({"organization_id": org_id})
        print(f"Found slack_token: {bool(slack_token)}")
        if slack_token:
            print(f"Token Org ID (slack): {slack_token.organization_id!r}")
            
        if not slack_token:
            missing_providers.append("slack")
            
    print("==========================================")
            
    if "github" in required_providers:
        if not await GitHubTokenDocument.find_one({"organization_id": org_id}):
            missing_providers.append("github")

    if missing_providers:
        raise HTTPException(
            status_code=403,
            detail={
                "status": "authorization_required",
                "missing_providers": missing_providers,
                "message": f"Missing OAuth connections for: {', '.join(missing_providers)}"
            }
        )

    created_responses = []

    for task_req in body.tasks:
        from syncsphere.tasks.documents import TaskAutomation
        
        automations = []
        if task_req.automations:
            automations = [
                TaskAutomation(action=a.action, config=a.config, status="pending") 
                for a in task_req.automations
            ]

        logger.info(
            "confirm-plan processing task",
            extra={
                "request_id": correlation_id,
                "task_title": task_req.title,
                "integrations_count": len(automations)
            }
        )

        doc = TaskDocument(
            org_id=org_id,
            title=task_req.title,
            description=task_req.description,
            assigned_to=task_req.assigned_to,
            priority=task_req.priority,
            status=task_req.status,
            due_date=task_req.due_date,
            automations=automations,
        )

        await doc.insert()

        if doc.automations:
            asyncio.create_task(_execute_task_automation(doc))
        else:
            # Fallback for standard tasks without automation requests
            asyncio.create_task(_fire_task_created_workflows(doc))
            asyncio.create_task(_post_slack_message_legacy(doc))

        created_responses.append(_doc_to_response(doc))

    return {
        "data": created_responses,
        "meta": ResponseMeta(request_id=correlation_id),
    }


@router.post(
    "/{task_id}/execute-automation",
    response_model=ResponseEnvelope[TaskResponse],
    status_code=status.HTTP_200_OK,
    summary="Manually execute or retry automation associated with a task",
)
async def execute_task_automation(
    request: Request,
    task_id: str,
    claims: dict = Depends(verify_jwt),
) -> dict:
    correlation_id = getattr(request.state, "correlation_id", None)
    org_id = claims["org"]

    try:
        oid = PydanticObjectId(task_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid task ID format.")

    doc = await TaskDocument.find_one({"_id": oid, "org_id": org_id, "deleted_at": None})
    if not doc:
        raise HTTPException(status_code=404, detail="Task not found.")

    if not doc.automations:
        raise HTTPException(status_code=400, detail="Task is not configured for automation.")

    doc = await _execute_task_automation_impl(doc)

    return {
        "data": _doc_to_response(doc),
        "meta": ResponseMeta(request_id=correlation_id),
    }


async def _execute_task_automation(doc: TaskDocument) -> None:
    # Re-fetch document from DB to avoid detached motor sessions in background tasks
    fresh_doc = await TaskDocument.get(doc.id)
    if fresh_doc:
        await _execute_task_automation_impl(fresh_doc)


async def _execute_task_automation_impl(doc: TaskDocument) -> TaskDocument:
    try:
        from syncsphere.workflow.application.action_registry import get_action
        from syncsphere.tasks.documents import WorkflowExecutionLogDocument, ActionResult

        log_doc = WorkflowExecutionLogDocument(
            workflow_id=str(doc.id),
            workflow_name=f"Task Automation - {doc.title}",
            organization_id=doc.org_id,
            status="running"
        )
        await log_doc.insert()
        has_failure = False

        for idx, auto in enumerate(doc.automations):
            doc.automations[idx].status = "executing"
            await doc.save()

            action_result = ActionResult(
                action=auto.action,
                status="running",
                input_summary={"config": auto.config}
            )

            try:
                # OAuth Check based on action prefix
                from syncsphere.tasks.documents import GoogleTokenDocument, SlackTokenDocument, GitHubTokenDocument
                provider_prefix = auto.action.split(".")[0]
                missing_oauth = False

                if provider_prefix in ["gmail", "google_calendar", "google_sheets", "google"]:
                    has_token = await GoogleTokenDocument.find_one({"organization_id": doc.org_id})
                    if not has_token:
                        missing_oauth = True
                        provider = "google"
                elif provider_prefix == "slack":
                    has_token = await SlackTokenDocument.find_one({"organization_id": doc.org_id})
                    if not has_token:
                        missing_oauth = True
                        provider = "slack"
                elif provider_prefix == "github":
                    has_token = await GitHubTokenDocument.find_one({"organization_id": doc.org_id})
                    if not has_token:
                        missing_oauth = True
                        provider = "github"

                if missing_oauth:
                    error_msg = {"status": "blocked", "reason": "missing_oauth", "provider": provider}
                    raise Exception(str(error_msg))

                action_fn = get_action(auto.action)
                result = await action_fn(**auto.config, organization_id=doc.org_id)

                doc.automations[idx].status = "success"
                doc.automations[idx].result = result
                doc.automations[idx].error = None
                
                action_result.status = "success"
                action_result.output_summary = result or {}

            except Exception as exc:
                import traceback
                logger.error("Task automation %s failed: %s %s", auto.action, exc, traceback.format_exc())
                
                from syncsphere.connectors.application.exceptions import OAuthError
                
                is_auth_error = (
                    isinstance(exc, OAuthError) or 
                    "missing_oauth" in str(exc) or 
                    "please connect" in str(exc).lower() or 
                    "revoked" in str(exc).lower() or
                    "permission" in str(exc).lower() or
                    "not in channel" in str(exc).lower() or
                    "missing_scope" in str(exc).lower()
                )
                
                if is_auth_error:
                    doc.automations[idx].status = "blocked"
                    doc.automations[idx].error = str(exc)
                    action_result.status = "blocked"
                else:
                    doc.automations[idx].status = "failed"
                    doc.automations[idx].error = str(exc)
                    has_failure = True
                    action_result.status = "failed"
                
                action_result.error = str(exc)


                action_result.completed_at = datetime.utcnow()
            doc.automations[idx].executed_at = datetime.utcnow()
            log_doc.action_results.append(action_result)
            await doc.save()

            logger.info(
                "Task automation executed",
                extra={
                    "task_id": str(doc.id),
                    "action": auto.action,
                    "status": action_result.status,
                    "error": action_result.error,
                    "sanitized_keys": list(auto.config.keys()),
                }
            )

        log_doc.status = "failed" if has_failure else "success"
        if has_failure and any(a.status == "success" for a in doc.automations):
            log_doc.status = "partial"
        log_doc.completed_at = datetime.utcnow()
        await log_doc.save()

        doc.status = "Completed" if not has_failure else "Pending"
        await doc.save()

    except Exception as exc:
        import traceback
        logger.error("Task automation execution failed globally: %s \n%s", exc, traceback.format_exc())

    return doc




# ---------------------------------------------------------------------------
# GET /v1/tasks — List tasks
# ---------------------------------------------------------------------------

@router.get(
    "",
    response_model=ResponseEnvelope[List[TaskResponse]],
    status_code=status.HTTP_200_OK,
    summary="List all tasks for the current organization",
)
async def list_tasks(
    request: Request,
    priority: Optional[str] = None,
    task_status: Optional[str] = None,
    claims: dict = Depends(verify_jwt),
) -> dict:
    correlation_id = getattr(request.state, "correlation_id", None)
    org_id = claims["org"]

    query: dict = {"org_id": org_id, "deleted_at": None}
    if priority:
        query["priority"] = priority
    if task_status:
        query["status"] = task_status

    docs = await TaskDocument.find(query).sort("-created_at").to_list()

    return {
        "data": [_doc_to_response(d) for d in docs],
        "meta": ResponseMeta(request_id=correlation_id),
    }


# ---------------------------------------------------------------------------
# GET /v1/tasks/{task_id} — Get single task
# ---------------------------------------------------------------------------

@router.get(
    "/{task_id}",
    response_model=ResponseEnvelope[TaskResponse],
    status_code=status.HTTP_200_OK,
    summary="Get a single task by ID",
)
async def get_task(
    request: Request,
    task_id: str,
    claims: dict = Depends(verify_jwt),
) -> dict:
    correlation_id = getattr(request.state, "correlation_id", None)
    org_id = claims["org"]

    try:
        oid = PydanticObjectId(task_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid task ID format.")

    doc = await TaskDocument.find_one({"_id": oid, "org_id": org_id, "deleted_at": None})
    if not doc:
        raise HTTPException(status_code=404, detail="Task not found.")

    return {
        "data": _doc_to_response(doc),
        "meta": ResponseMeta(request_id=correlation_id),
    }


# ---------------------------------------------------------------------------
# PUT /v1/tasks/{task_id} — Update task
# ---------------------------------------------------------------------------

@router.put(
    "/{task_id}",
    response_model=ResponseEnvelope[TaskResponse],
    status_code=status.HTTP_200_OK,
    summary="Update a task",
)
async def update_task(
    request: Request,
    task_id: str,
    body: UpdateTaskRequest,
    claims: dict = Depends(verify_jwt),
) -> dict:
    correlation_id = getattr(request.state, "correlation_id", None)
    org_id = claims["org"]

    try:
        oid = PydanticObjectId(task_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid task ID format.")

    doc = await TaskDocument.find_one({"_id": oid, "org_id": org_id, "deleted_at": None})
    if not doc:
        raise HTTPException(status_code=404, detail="Task not found.")

    update_data = body.model_dump(exclude_none=True)
    for field, value in update_data.items():
        setattr(doc, field, value)

    await doc.save()

    return {
        "data": _doc_to_response(doc),
        "meta": ResponseMeta(request_id=correlation_id),
    }


# ---------------------------------------------------------------------------
# DELETE /v1/tasks/{task_id} — Soft-delete task
# ---------------------------------------------------------------------------

@router.delete(
    "/{task_id}",
    response_model=ResponseEnvelope[bool],
    status_code=status.HTTP_200_OK,
    summary="Delete a task (soft delete)",
)
async def delete_task(
    request: Request,
    task_id: str,
    claims: dict = Depends(verify_jwt),
) -> dict:
    correlation_id = getattr(request.state, "correlation_id", None)
    org_id = claims["org"]

    try:
        oid = PydanticObjectId(task_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid task ID format.")

    doc = await TaskDocument.find_one({"_id": oid, "org_id": org_id, "deleted_at": None})
    if not doc:
        raise HTTPException(status_code=404, detail="Task not found.")

    doc.deleted_at = datetime.utcnow()
    await doc.save()

    return {
        "data": True,
        "meta": ResponseMeta(request_id=correlation_id),
    }
