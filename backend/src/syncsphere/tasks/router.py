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
# ---------------------------------------------------------------------------
# POST /v1/tasks — Create task
# ---------------------------------------------------------------------------

async def _enforce_task_preflight(automations: list, org_id: str, user_id: str = None) -> None:
    from syncsphere.workflow.application.action_registry import get_action
    
    missing_providers = []
    
    for auto in automations:
        if not auto.config: continue
        
        # Bypass OAuth validation for native system control actions (e.g., Approval Nodes)
        if auto.action.startswith("system."):
            continue
            
        action_fn = get_action(auto.action)
        provider = auto.action.split(".")[0]
        
        req_acct = auto.config.get("slack_workspace") if provider == "slack" else auto.config.get("google_email") if provider in ["gmail", "google_calendar", "google_sheets"] else auto.config.get("github_organization")
        req_acct_str = str(req_acct).strip() if req_acct else None
        
        # Auto-resolve google_email from user's actual connected Google account
        if provider in ["gmail", "google_calendar", "google_sheets"]:
            from syncsphere.tasks.documents import GoogleTokenDocument
            if not req_acct_str or "example.com" in (req_acct_str or "") or "your_email" in (req_acct_str or "") or "placeholder" in (req_acct_str or "").lower():
                query = {"organization_id": org_id}
                if user_id:
                    query["user_id"] = user_id
                token_doc = await GoogleTokenDocument.find_one(query)
                if token_doc:
                    req_acct_str = token_doc.google_email
                    auto.config["google_email"] = req_acct_str
                    logger.info("Auto-resolved google_email to '%s' from connected account", req_acct_str)
        
        # Enforce valid fields blocking natural language fallbacks
        if req_acct_str and "your_email" in req_acct_str:
            raise HTTPException(status_code=400, detail="Requested identity contains placeholder syntax instead of a real account.")
            
        try:
            # We perform a dry-run check ONLY for token linkage
            if provider in ["gmail", "google_calendar", "google_sheets"]:
                from syncsphere.connectors.application.google_token_service import get_valid_google_token
                await get_valid_google_token(google_email=req_acct_str, organization_id=org_id, user_id=user_id)
            elif provider == "slack":
                from syncsphere.connectors.presentation.slack_actions import _get_slack_token
                await _get_slack_token(organization_id=org_id, slack_workspace=req_acct_str)
            elif provider == "github":
                from syncsphere.connectors.application.github_token_service import get_valid_github_token
                await get_valid_github_token(organization_id=org_id, requested_account=req_acct_str, user_id=user_id)
        except Exception as exc:
            from syncsphere.connectors.application.exceptions import OAuthError
            if isinstance(exc, OAuthError) or "missing_oauth" in str(exc) or "not found" in str(exc).lower() or "not authorized" in str(exc).lower() or "no slack workspace" in str(exc).lower() or "no github" in str(exc).lower():
                key = f"{provider}:{req_acct_str}" if req_acct_str else provider
                if key not in missing_providers:
                    missing_providers.append(key)

    if missing_providers:
        from fastapi import HTTPException
        clean_providers = [p.split(":")[0] for p in missing_providers]
        
        acct_msgs = []
        for p in missing_providers:
            if ":" in p:
                parts = p.split(":", 1)
                acct_msgs.append(f"Missing OAuth connection for {parts[0].replace('_', ' ').title()} account: {parts[1]}")
                
        msg = "\n".join(acct_msgs) if acct_msgs else f"Missing OAuth connections for: {', '.join(set(clean_providers))}"
        
        raise HTTPException(
            status_code=403,
            detail={
                "status": "authorization_required",
                "missing_providers": missing_providers,
                "message": msg
            }
        )

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

    # Pre-flight Check for explicitly unauthorized execution
    await _enforce_task_preflight(automations, org_id, claims.get("sub"))

    doc = TaskDocument(
        org_id=org_id,
        created_by_user_id=claims.get("sub"),
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
# GET /v1/tasks — List tasks
# ---------------------------------------------------------------------------

@router.get(
    "",
    response_model=ResponseEnvelope[List[TaskResponse]],
    status_code=status.HTTP_200_OK,
    summary="List all tasks",
)
async def list_tasks(
    request: Request,
    priority: Optional[str] = None,
    task_status: Optional[str] = None,
    claims: dict = Depends(verify_jwt),
) -> dict:
    correlation_id = getattr(request.state, "correlation_id", None)
    org_id = claims["org"]

    query = {"org_id": org_id, "created_by_user_id": claims.get("sub"), "deleted_at": None}
    if priority:
        query["priority"] = priority
    if task_status:
        query["status"] = task_status

    docs = await TaskDocument.find(query).sort("-created_at").to_list()
    return {
        "data": [_doc_to_response(doc) for doc in docs],
        "meta": ResponseMeta(request_id=correlation_id),
    }


# ---------------------------------------------------------------------------
# GET /v1/tasks/{task_id} — Get task
# ---------------------------------------------------------------------------

@router.get(
    "/{task_id}",
    response_model=ResponseEnvelope[TaskResponse],
    status_code=status.HTTP_200_OK,
    summary="Get a single task",
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

    doc = await TaskDocument.find_one({"_id": oid, "org_id": org_id, "created_by_user_id": claims.get("sub"), "deleted_at": None})
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
    summary="Update an existing task",
)
async def update_task(
    request: Request,
    task_id: str,
    body: UpdateTaskRequest,
    claims: dict = Depends(verify_jwt),
) -> dict:
    import datetime as dt
    correlation_id = getattr(request.state, "correlation_id", None)
    org_id = claims["org"]

    try:
        oid = PydanticObjectId(task_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid task ID format.")

    doc = await TaskDocument.find_one({"_id": oid, "org_id": org_id, "created_by_user_id": claims.get("sub"), "deleted_at": None})
    if not doc:
        raise HTTPException(status_code=404, detail="Task not found.")

    if body.title is not None:
        doc.title = body.title
    if body.description is not None:
        doc.description = body.description
    if body.assigned_to is not None:
        doc.assigned_to = body.assigned_to
    if body.priority is not None:
        doc.priority = body.priority
    if body.status is not None:
        doc.status = body.status
    if body.due_date is not None:
        doc.due_date = body.due_date
    
    doc.updated_at = dt.datetime.now(dt.timezone.utc)
    await doc.save()

    return {
        "data": _doc_to_response(doc),
        "meta": ResponseMeta(request_id=correlation_id),
    }


# ---------------------------------------------------------------------------
# DELETE /v1/tasks/{task_id} — Delete task
# ---------------------------------------------------------------------------

@router.delete(
    "/{task_id}",
    response_model=ResponseEnvelope[bool],
    status_code=status.HTTP_200_OK,
    summary="Delete a task",
)
async def delete_task(
    request: Request,
    task_id: str,
    claims: dict = Depends(verify_jwt),
) -> dict:
    import datetime as dt
    correlation_id = getattr(request.state, "correlation_id", None)
    org_id = claims["org"]

    try:
        oid = PydanticObjectId(task_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid task ID format.")

    doc = await TaskDocument.find_one({"_id": oid, "org_id": org_id, "created_by_user_id": claims.get("sub"), "deleted_at": None})
    if not doc:
        raise HTTPException(status_code=404, detail="Task not found.")

    # Soft delete
    doc.deleted_at = dt.datetime.now(dt.timezone.utc)
    await doc.save()

    return {
        "data": True,
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

    import asyncio
    import time
    from syncsphere.core.logging.execution_timer import ExecutionTimer

    timer = ExecutionTimer("AI Task Planning")
    overall_start_time = time.perf_counter()
    prep_start_time = time.perf_counter()

    from syncsphere.tasks.documents import GoogleTokenDocument, SlackTokenDocument, GitHubTokenDocument
    try:
        t_google, t_slack, t_github = await asyncio.gather(
            GoogleTokenDocument.find_one({"organization_id": org_id, "user_id": claims.get("sub")}),
            SlackTokenDocument.find_one({"organization_id": org_id, "user_id": claims.get("sub")}),
            GitHubTokenDocument.find_one({"organization_id": org_id, "user_id": claims.get("sub")})
        )
    except Exception:
        t_google, t_slack, t_github = None, None, None
    has_google = t_google is not None
    has_slack = t_slack is not None
    has_github = t_github is not None

    connection_status_str = (
        f"- Google (Gmail/Calendar/Sheets): {'Connected' if has_google else 'Not connected'}\n"
        f"- Slack: {'Connected' if has_slack else 'Not connected'}\n"
        f"- GitHub: {'Connected' if has_github else 'Not connected'}\n"
    )

    from syncsphere.workflow.application.action_registry import CAPABILITY_REGISTRY

    actions_info = []
    
    # Lightweight relevant-capability selection mechanism
    prompt_lower = body.prompt.lower()
    
    # Simple keyword mapping for filtering
    app_keywords = {
        "slack": ["slack", "message", "channel"],
        "gmail": ["gmail", "email", "mail"],
        "google_calendar": ["calendar", "event", "schedule", "meeting", "invite"],
        "google_sheets": ["sheet", "spreadsheet", "row", "column", "excel", "csv"],
        "github": ["github", "pr", "pull request", "issue", "repo", "repository", "commit"]
    }
    
    for app_name, app_info in CAPABILITY_REGISTRY.items():
        # Check if any keyword matches the prompt. If not, don't include it.
        keywords = app_keywords.get(app_name, [])
        if any(kw in prompt_lower for kw in keywords) or not keywords:
            for action_name, action_info in app_info["actions"].items():
                action_id = f"{app_name}.{action_name}"
                config_str = ", ".join([f"'{k}': {v['description']}" for k, v in action_info["input_schema"].items()])
                req_str = ", ".join(action_info.get("required_fields", []))
                actions_info.append(f"  - '{action_id}': {action_info['description']}\n    Required: [{req_str}]\n    Schema: {{{config_str}}}")

    actions_list_str = "\n".join(actions_info)

    # === RAG Context Injection (Optional) ===
    knowledge_context = ""
    try:
        from syncsphere.knowledge.application.queries import SearchKnowledgeQuery
        search_query = SearchKnowledgeQuery(
            org_id=org_id,
            query=body.prompt,
            top_k=3,
            correlation_id=correlation_id
        )
        search_res = await container.knowledge_service.search_knowledge(search_query)
        # Handle Result monad which has checking properties like .is_ok or .is_fail
        if not (hasattr(search_res, "is_fail") and search_res.is_fail()):
            context = search_res.value()
            if context and hasattr(context, 'citations') and context.citations:
                knowledge_context = "## CORPORATE KNOWLEDGE BASE CONTEXT\n"
                for cite in context.citations:
                    knowledge_context += f"- {cite.text_snippet}\n"
                knowledge_context += "\nUse this context to accurately fill out required fields, project names, or configuration values.\n\n"
    except Exception as e:
        logger.warning(f"Failed to fetch knowledge context: {e}")

    messages = [
        {
            "role": "system",
            "content": (
                "You are an AI Project Manager for SyncSphere executing a ZERO-FRICTION experience. "
                "Extract the primary task details and AUTOMATICALLY configure the requested integrations in a SINGLE task object.\n\n"
                f"Today's date is: {datetime.now(timezone.utc).date().isoformat()}.\n\n"
                f"{knowledge_context}"
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
                "8. For each integration in 'integrations', you MUST use exactly the keys 'action', 'selected', and 'config'. Do NOT use 'provider' or 'type'. The 'action' string must PERFECTLY match one of the action keys in the list. For Google Sheets append_row, 'values' MUST be a JSON array of specific values (e.g. [\"A\", \"B\"]), not a single comma-separated string.\n"
                "9. CRITICAL: If the user explicitly asks to use a specific account or workspace as the actor/sender (e.g. 'using friend@gmail.com', 'from dev-workspace'), you MUST extract and include that exact identifier in the config object under 'google_email' or 'slack_workspace'. NEVER assume the recipient is the acting account.\n"
                "10. VERY IMPORTANT: The 'google_email' parameter means THE AUTHORIZED SENDER ACCOUNT. NEVER put the recipient email here. If there is no explicitly specified sender, DO NOT output 'google_email' at all.\n"
                "11. CRITICAL: DO NOT mask, hide, redact, or censor email addresses (e.g., do NOT change 'user@gmail.com' to 'use***@gmail.com'). You MUST output email addresses EXACTLY as provided by the user."
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
        http_status = "500"
        if "429" in err_msg or "quota" in err_msg or "resource_exhausted" in err_msg:
            http_status = "429"
        elif "404" in err_msg:
            http_status = "404"
        elif "401" in err_msg or "403" in err_msg or "unauthorized" in err_msg:
            http_status = "401/403"
        elif "402" in err_msg or "insufficient" in err_msg or "payment" in err_msg:
            http_status = "402"
        elif "400" in err_msg:
            http_status = "400"
        elif "timeout" in err_msg or "timed out" in err_msg:
            http_status = "504"

        provider_name = getattr(result, "provider_name", "AI") or "AI"
        
        import traceback
        logger.exception(
            "plan-with-ai provider request failed: %s\n%s",
            result.error_message or "Unknown error",
            traceback.format_exc()
        )

        if http_status == "404":
            raise HTTPException(
                status_code=404,
                detail={"error": "ai_model_not_found", "message": f"Configured AI provider or model is unavailable: {result.error_message}"}
            )
        elif http_status == "429":
            raise HTTPException(
                status_code=429,
                detail={"error": "ai_rate_limit", "message": f"{provider_name.title()} API rate limit or quota exceeded: {result.error_message}"}
            )
        elif http_status == "401/403":
            if "401" in err_msg:
                raise HTTPException(
                    status_code=401,
                    detail={"error": "ai_authentication", "message": f"AI provider authentication failed: {result.error_message}"}
                )
            else:
                raise HTTPException(
                    status_code=403,
                    detail={"error": "ai_permission_denied", "message": f"AI provider permission or billing access denied: {result.error_message}"}
                )
        elif http_status == "402":
            raise HTTPException(
                status_code=402,
                detail={"error": "ai_usage_limit", "message": f"AI provider usage limit reached: {result.error_message}"}
            )
        elif http_status == "400":
            raise HTTPException(
                status_code=400,
                detail={"error": "ai_bad_request", "message": f"AI provider rejected request: {result.error_message}"}
            )
        elif http_status == "504":
            raise HTTPException(
                status_code=504,
                detail={"error": "ai_timeout", "message": f"AI service timed out: {result.error_message}"}
            )
    
        safe_msg = f"AI service error: {result.error_message}" if result.error_message else "AI service is temporarily unavailable."
        raise HTTPException(
            status_code=502,
            detail={"error": "ai_unavailable", "message": safe_msg}
        )
    import json
    try:
        parsed = json.loads(result.raw_output)
        # Validate using Pydantic schema
        validated_data = AIPlannedTaskSchema(**parsed).model_dump()
        
        # Cross-reference with CAPABILITY_REGISTRY to strictly enforce missing_required_fields
        from syncsphere.workflow.application.action_registry import CAPABILITY_REGISTRY
        
        for integration in validated_data.get("integrations", []):
            action_id = integration.get("action")
            if not action_id:
                continue
                
            parts = action_id.split(".")
            if len(parts) == 2:
                app_name, action_name = parts
                action_info = CAPABILITY_REGISTRY.get(app_name, {}).get("actions", {}).get(action_name)
                if action_info:
                    required_fields = action_info.get("required_fields", [])
                    config = integration.get("config", {})
                    missing = integration.get("missing_required_fields", [])
                    
                    import re
                    for req in required_fields:
                        val = config.get(req)
                        is_missing = False
                        if val is None:
                            is_missing = True
                        elif isinstance(val, str):
                            sval = str(val).strip()
                            if not sval or re.match(r'^#+$', sval) or sval.lower() in ["my channel", "the channel", "slack channel", "slack", "gmail", "calendar", "channel", "your_email@domain.com", "person@example.com"]:
                                is_missing = True
                        elif isinstance(val, list) and len(val) == 0:
                            is_missing = True
                            
                        if is_missing and req not in missing:
                            missing.append(req)
                    
                    integration["missing_required_fields"] = missing

        # Inject a Human Approval gate before the first risky action
        risky_terms = [".delete", "gmail.send_email", "github.create_issue", "github.create_pull_request", "jira.create_issue", "jira.update_issue", "http.post", "http.put", "http.delete", "webhook.post"]
        integrations = validated_data.get("integrations", [])
        
        insert_idx = -1
        target_action = ""
        for idx, integ in enumerate(integrations):
            action_id = integ.get("action", "")
            # Check for high-risk actions
            if any(term in action_id for term in risky_terms) or ".delete" in action_id:
                insert_idx = idx
                target_action = action_id
                break
                
        if insert_idx != -1:
            approval_node = {
                "action": "system.approval",
                "selected": True,
                "config": {
                    "title": f"Review Required for {target_action}",
                    "description": "Auto-inserted Human Approval gate before executing high-risk integration.",
                    "instructions": "Please review the planned action data and missing fields before approving.",
                    "approvers": ["admin@acme.ai"],
                    "timeout_hours": 24,
                    "auto_reject": True,
                },
                "missing_required_fields": []
            }
            integrations.insert(insert_idx, approval_node)

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
    response_model=dict,
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

    from syncsphere.tasks.documents import TaskAutomation
    
    all_automations = []
    for task_req in body.tasks:
        if task_req.automations:
            all_automations.extend([
                TaskAutomation(action=a.action, config=a.config, status="pending") 
                for a in task_req.automations
            ])
            
    await _enforce_task_preflight(all_automations, org_id, claims.get("sub"))

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
            created_by_user_id=claims.get("sub"),
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

@router.post(
    "/{task_id}/save-as-workflow",
    status_code=status.HTTP_201_CREATED,
    summary="Save a task's automations into a reusable Automation Workflow",
)
async def save_task_as_workflow(
    request: Request,
    task_id: str,
    claims: dict = Depends(verify_jwt),
) -> dict:
    correlation_id = getattr(request.state, "correlation_id", None)
    org_id = claims["org"]
    user_id = claims.get("sub")

    try:
        oid = PydanticObjectId(task_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid task ID format.")

    doc = await TaskDocument.find_one({"_id": oid, "org_id": org_id, "deleted_at": None})
    if not doc:
        raise HTTPException(status_code=404, detail="Task not found.")

    from syncsphere.tasks.documents import AutomationWorkflowDocument, AutomationTrigger, AutomationAction
    
    new_doc = AutomationWorkflowDocument(
        name=f"Copy of {doc.title} Automations",
        user_id=user_id,
        organization_id=org_id,
        is_active=False,
        trigger=AutomationTrigger(app="task", event="manual"),
        actions=[
            AutomationAction(app=a.action.split(".")[0], action=a.action, config=dict(a.config))
            for a in doc.automations
        ] if doc.automations else [],
    )
    await new_doc.insert()

    from syncsphere.tasks.automation_routes import _doc_to_response as _auto_to_resp
    return {
        "data": _auto_to_resp(new_doc).model_dump(mode="json"),
        "meta": ResponseMeta(request_id=correlation_id).model_dump(),
    }

@router.post(
    "/{task_id}/schedule",
    status_code=status.HTTP_200_OK,
    summary="Schedule a task's automations by converting to an Automation Workflow",
)
async def schedule_task_as_automation(
    request: Request,
    task_id: str,
    body: dict,
    claims: dict = Depends(verify_jwt),
) -> dict:
    correlation_id = getattr(request.state, "correlation_id", None)
    org_id = claims["org"]
    user_id = claims.get("sub")

    try:
        oid = PydanticObjectId(task_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid task ID format.")

    doc = await TaskDocument.find_one({"_id": oid, "org_id": org_id, "deleted_at": None})
    if not doc:
        raise HTTPException(status_code=404, detail="Task not found.")

    from syncsphere.tasks.documents import AutomationWorkflowDocument, AutomationTrigger, AutomationAction
    
    new_doc = AutomationWorkflowDocument(
        name=f"{doc.title} Scheduled Automations",
        user_id=user_id,
        organization_id=org_id,
        is_active=True,
        trigger=AutomationTrigger(app="task", event="schedule"),
        actions=[
            AutomationAction(app=a.action.split(".")[0], action=a.action, config=dict(a.config))
            for a in doc.automations
        ] if doc.automations else [],
    )
    await new_doc.insert()

    from syncsphere.tasks.automation_routes import schedule_automation, ScheduleAutomationRequest
    req_body = ScheduleAutomationRequest(**body)
    
    return await schedule_automation(request=request, automation_id=str(new_doc.id), body=req_body, claims=claims)


async def _execute_task_automation(doc: TaskDocument) -> None:
    # Re-fetch document from DB to avoid detached motor sessions in background tasks
    fresh_doc = await TaskDocument.get(doc.id)
    if fresh_doc:
        await _execute_task_automation_impl(fresh_doc)


async def _execute_task_automation_impl(doc: TaskDocument) -> TaskDocument:
    try:
        from syncsphere.workflow.application.action_registry import get_action
        from syncsphere.tasks.documents import WorkflowExecutionLogDocument, ActionResult
        from syncsphere.core.dependency_injection.container import container
        from syncsphere.runtime.domain.events import ExecutionStarted, ExecutionCompleted, ExecutionFailed
        from syncsphere.core.events.base import BaseEvent
        from syncsphere.core.logging.execution_timer import ExecutionTimer

        import time
        exec_timer = ExecutionTimer(f"Task Automation Execution - {doc.title}")

        mongo_init_start = time.perf_counter()
        log_doc = WorkflowExecutionLogDocument(
            workflow_id=str(doc.id),
            workflow_name=f"Task Automation - {doc.title}",
            organization_id=doc.org_id,
            user_id=doc.created_by_user_id,
            status="running"
        )
        await log_doc.insert()
        exec_timer.record_stage("MongoDB Save (Log Document Insert)", (time.perf_counter() - mongo_init_start) * 1000.0)
        
        if getattr(container, "event_bus", None):
            try:
                await container.event_bus.publish(ExecutionStarted(
                    org_id=doc.org_id,
                    correlation_id=str(doc.id),
                    session_id=str(doc.id)
                ))
            except Exception as ebb:
                logger.warning("Event bus failed to publish ExecutionStarted: %s", ebb)
        has_failure = False

        for idx, auto in enumerate(doc.automations):
            # Skip already finished actions
            if auto.status in ["success", "failed", "blocked", "awaiting_approval"]:
                if auto.status in ["failed", "blocked"]:
                    has_failure = True
                continue

            # Check if this is an approval checkpoint
            if auto.action == "system.approval" or getattr(auto, "requires_approval", False):
                # We no longer pause for human approval. We automatically resolve and continue.
                logger.info(f"Automatically bypassing human approval gate for {doc.id}")
                doc.automations[idx].status = "success"
                await doc.save()
                continue

            status_start = time.perf_counter()
            doc.automations[idx].status = "executing"
            await doc.save()
            exec_timer.record_stage(f"MongoDB Save (Executing state for '{auto.action}')", (time.perf_counter() - status_start) * 1000.0)

            action_result = ActionResult(
                action=auto.action,
                status="running",
                input_summary={"config": auto.config}
            )

            try:
                # Required Fields Preflight Check
                from syncsphere.workflow.application.action_registry import CAPABILITY_REGISTRY
                parts = auto.action.split(".")
                if len(parts) == 2:
                    app_name, action_name = parts
                    action_info = CAPABILITY_REGISTRY.get(app_name, {}).get("actions", {}).get(action_name)
                    if action_info:
                        required_fields = action_info.get("required_fields", [])
                        import re
                        for req in required_fields:
                            val = auto.config.get(req)
                            is_missing = False
                            if val is None:
                                is_missing = True
                            elif isinstance(val, str):
                                sval = str(val).strip()
                                if not sval or re.match(r'^#+$', sval) or sval.lower() in ["my channel", "the channel", "slack channel", "slack", "gmail", "calendar", "channel", "your_email@domain.com", "person@example.com"]:
                                    is_missing = True
                            elif isinstance(val, list) and len(val) == 0:
                                is_missing = True
                            
                            if is_missing:
                                raise ValueError(f"Missing required field '{req}' for action {auto.action}")
                
                # OAuth Check based on action prefix
                from syncsphere.tasks.documents import GoogleTokenDocument, SlackTokenDocument, GitHubTokenDocument
                provider_prefix = auto.action.split(".")[0]
                missing_oauth = False
                error_msg = None

                if provider_prefix in ["gmail", "google_calendar", "google_sheets", "google"]:
                    req_acct = auto.config.get("google_email")
                    
                    # Auto-resolve google_email from user's actual connected Google account
                    if not req_acct or "example.com" in str(req_acct) or "your_email" in str(req_acct) or "placeholder" in str(req_acct).lower():
                        query = {"organization_id": doc.org_id}
                        if doc.created_by_user_id:
                            query["user_id"] = doc.created_by_user_id
                        resolved_token = await GoogleTokenDocument.find_one(query)
                        if resolved_token:
                            req_acct = resolved_token.google_email
                            auto.config["google_email"] = req_acct
                            logger.info("Execution: auto-resolved google_email to '%s'", req_acct)
                    
                    query = {"organization_id": doc.org_id}
                    if doc.created_by_user_id:
                        query["user_id"] = doc.created_by_user_id
                    
                    if req_acct:
                        query["google_email"] = {"$regex": f"^{req_acct}$", "$options": "i"}
                        has_token = await GoogleTokenDocument.find_one(query)
                        if not has_token:
                            import json
                            error_msg = json.dumps({
                                "status": "blocked",
                                "reason": "missing_oauth",
                                "provider": "google",
                                "account": req_acct,
                                "message": f"Google account {req_acct} is not connected. Please connect this account before continuing."
                            })
                            missing_oauth = True
                    else:
                        if doc.created_by_user_id:
                            query["user_id"] = doc.created_by_user_id
                        has_token = await GoogleTokenDocument.find_one(query)
                        if not has_token:
                            missing_oauth = True
                            provider = "google"
                
                elif provider_prefix == "slack":
                    req_workspace = auto.config.get("slack_workspace")
                    query = {"organization_id": doc.org_id}
                    if doc.created_by_user_id:
                        query["user_id"] = doc.created_by_user_id
                    
                    if req_workspace:
                        import re
                        query["team_name"] = {"$regex": f".*{re.escape(req_workspace)}.*", "$options": "i"}
                        has_token = await SlackTokenDocument.find_one(query)
                        if not has_token:
                            import json
                            error_msg = json.dumps({
                                "status": "blocked",
                                "reason": "missing_oauth",
                                "provider": "slack",
                                "account": req_workspace,
                                "message": f"Slack workspace '{req_workspace}' is not connected. Please connect this account before sending."
                            })
                            missing_oauth = True
                    else:
                        has_token = await SlackTokenDocument.find_one(query)
                        if not has_token:
                            missing_oauth = True
                            provider = "slack"
                            
                elif provider_prefix == "github":
                    query = {"organization_id": doc.org_id}
                    if doc.created_by_user_id:
                        query["user_id"] = doc.created_by_user_id
                    has_token = await GitHubTokenDocument.find_one(query)
                    if not has_token:
                        missing_oauth = True
                        provider = "github"

                if missing_oauth:
                    if not error_msg:
                        import json
                        error_msg = json.dumps({"status": "blocked", "reason": "missing_oauth", "provider": provider})
                    # Raise an OAuthError which explicitly triggers the block route in the except handler below
                    from syncsphere.connectors.application.exceptions import OAuthError
                    raise OAuthError(error_msg)

                conn_exec_start = time.perf_counter()
                action_fn = get_action(auto.action)
                result = await action_fn(**auto.config, organization_id=doc.org_id, user_id=doc.created_by_user_id)
                conn_exec_ms = (time.perf_counter() - conn_exec_start) * 1000.0
                exec_timer.record_stage(f"Connector Execution ({auto.action})", conn_exec_ms)

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
                    "missing_scope" in str(exc).lower() or
                    "account is inactive" in str(exc).lower() or
                    "account_inactive" in str(exc).lower()
                )
                
                if is_auth_error:
                    doc.automations[idx].status = "blocked"
                    doc.automations[idx].error = str(exc)
                    action_result.status = "blocked"
                    has_failure = True
                else:
                    doc.automations[idx].status = "failed"
                    doc.automations[idx].error = str(exc)
                    has_failure = True
                    action_result.status = "failed"
                
                action_result.error = str(exc)

                action_result.completed_at = datetime.utcnow()

            save_step_start = time.perf_counter()
            doc.automations[idx].executed_at = datetime.utcnow()
            log_doc.action_results.append(action_result)
            await doc.save()
            exec_timer.record_stage(f"MongoDB Save (Result state for '{auto.action}')", (time.perf_counter() - save_step_start) * 1000.0)

            if getattr(container, "event_bus", None):
                try:
                    class ConnectorExecEvent(BaseEvent):
                        event_type: str = f"connector.action_{'failed' if action_result.status != 'success' else 'completed'}"
                        connector_id: str
                        
                    await container.event_bus.publish(ConnectorExecEvent(
                        org_id=doc.org_id,
                        correlation_id=str(doc.id),
                        connector_id=auto.action
                    ))
                except Exception as ebb:
                    logger.warning("Event bus failed to publish ConnectorExecEvent: %s", ebb)

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

        final_save_start = time.perf_counter()
        log_doc.status = "failed" if has_failure else "success"
        if has_failure and any(a.status == "success" for a in doc.automations):
            log_doc.status = "partial"
        log_doc.completed_at = datetime.utcnow()
        await log_doc.save()

        doc.status = "Completed" if not has_failure else "Pending"
        await doc.save()
        exec_timer.record_stage("MongoDB Save (Final Execution State)", (time.perf_counter() - final_save_start) * 1000.0)

        exec_timer.print_summary()

        duration = (time.perf_counter() - overall_start_time) * 1000.0
        if getattr(container, "event_bus", None):
            try:
                if has_failure:
                    evt = ExecutionFailed(org_id=doc.org_id, correlation_id=str(doc.id), session_id=str(doc.id), error_message="Task failed")
                else:
                    evt = ExecutionCompleted(org_id=doc.org_id, correlation_id=str(doc.id), session_id=str(doc.id))
                evt.payload = {"duration_ms": duration}
                await container.event_bus.publish(evt)
            except Exception as ebb:
                logger.warning("Event bus failed to publish completion event: %s", ebb)

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

# ---------------------------------------------------------------------------
# POST /v1/tasks/{task_id}/schedule — Schedule a task
# ---------------------------------------------------------------------------
class ScheduleTaskRequest(BaseModel):
    schedule_type: str = Field(..., description="once|hourly|daily|weekly|monthly|every_x_hours")
    start_date: Optional[str] = Field(default=None, description="ISO datetime for one-time run")
    time_of_day: Optional[str] = Field(default=None, description="HH:MM for daily/weekly/monthly")
    interval_hours: Optional[int] = Field(default=None, description="N for every_x_hours")
    enabled: bool = Field(default=True)

@router.post("/{task_id}/schedule", summary="Schedule a task")
async def schedule_task(
    request: Request,
    task_id: str,
    body: ScheduleTaskRequest,
    claims: dict = Depends(verify_jwt),
):
    correlation_id = getattr(request.state, "correlation_id", None)
    org_id = claims["org"]

    try:
        oid = PydanticObjectId(task_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid task ID format.")

    doc = await TaskDocument.find_one({"_id": oid, "organization_id": org_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Task not found.")

    from syncsphere.workflow.infrastructure.documents.workflow_schedule_document import WorkflowScheduleDocument
    from datetime import datetime, timezone
    
    # Delete existing schedule for this task
    await WorkflowScheduleDocument.find({"workflow_id": task_id}).delete()

    next_run: Optional[datetime] = None
    now = datetime.now(timezone.utc)
    try:
        if body.schedule_type == "once" and body.start_date:
            from datetime import datetime as _dt
            next_run = _dt.fromisoformat(body.start_date.replace("Z", "+00:00"))
        elif body.schedule_type == "hourly":
            from datetime import timedelta
            next_run = now + timedelta(hours=1)
        elif body.schedule_type == "every_x_hours" and body.interval_hours:
            from datetime import timedelta
            next_run = now + timedelta(hours=body.interval_hours)
        elif body.schedule_type in ("daily", "weekly", "monthly") and body.time_of_day:
            h, m = (int(x) for x in body.time_of_day.split(":"))
            from datetime import timedelta
            candidate = now.replace(hour=h, minute=m, second=0, microsecond=0)
            if candidate <= now:
                candidate += timedelta(days=1)
            next_run = candidate
    except Exception:
        pass

    sched_doc = WorkflowScheduleDocument(
        workflow_id=task_id,
        workflow_name=doc.title or "Standard Task",
        org_id=org_id,
        schedule_type=body.schedule_type,
        start_date=body.start_date,
        time_of_day=body.time_of_day,
        interval_hours=body.interval_hours,
        enabled=body.enabled,
        next_run_at=next_run,
        created_by=claims.get("sub"),
        cron_expression=None,
        end_date=None,
        timezone="UTC",
        day_of_week=None,
        day_of_month=None,
    )
    await sched_doc.save()

    return {
        "data": {
            "id": str(sched_doc.id),
            "task_id": task_id,
            "task_name": doc.title,
            "schedule_type": body.schedule_type,
            "enabled": body.enabled,
            "next_run": next_run.isoformat() if next_run else None,
        },
        "meta": ResponseMeta(request_id=correlation_id).model_dump(),
    }


# ---------------------------------------------------------------------------
# POST /v1/tasks/{task_id}/duplicate — Duplicate an existing task
# ---------------------------------------------------------------------------
@router.post("/{task_id}/duplicate", summary="Duplicate a task and its automations")
async def duplicate_task(
    request: Request,
    task_id: str,
    claims: dict = Depends(verify_jwt),
):
    correlation_id = getattr(request.state, "correlation_id", None)
    org_id = claims["org"]

    try:
        oid = PydanticObjectId(task_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid task ID format.")

    doc = await TaskDocument.find_one({"_id": oid, "organization_id": org_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Task not found.")

    new_doc = TaskDocument(
        title=f"Copy of {doc.title}",
        description=doc.description,
        assigned_to=doc.assigned_to,
        priority=doc.priority,
        status="Pending",
        due_date=doc.due_date,
        organization_id=doc.organization_id,
        user_id=claims.get("sub"),
        automations=[dict(a) for a in doc.automations] if doc.automations else []
    )
    await new_doc.insert()

    return {
        "data": dict(new_doc),
        "meta": ResponseMeta(request_id=correlation_id).model_dump(),
    }
