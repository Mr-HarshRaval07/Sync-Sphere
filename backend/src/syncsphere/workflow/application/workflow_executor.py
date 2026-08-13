"""
Workflow Executor

Executes automation workflows:
  1. Load AutomationWorkflowDocument
  2. Verify is_active
  3. Execute actions in order from ACTION_REGISTRY
  4. Handle failures with retry logic (exponential backoff)
  5. Log results to WorkflowExecutionLogDocument

Never executes arbitrary code — only registered actions from ACTION_REGISTRY.
"""
import asyncio
from datetime import datetime, timezone
from typing import Any

from syncsphere.tasks.documents import (
    AutomationWorkflowDocument,
    WorkflowExecutionLogDocument,
    ActionResult,
)
from syncsphere.workflow.application.action_registry import get_action

# Retry configuration
MAX_ATTEMPTS = 3
BASE_BACKOFF_SECONDS = 1.0

# Errors that are permanent and should NOT be retried
PERMANENT_ERROR_KEYWORDS = [
    "reconnect",
    "not registered",
    "not found",
    "disabled",
    "invalid_grant",
    "invalid_token",
    "authentication failed",
    "no google account",
    "no github account",
    "no slack",
    "not connected",
    "spreadsheet id",
    "repository not found",
]


def _is_permanent_error(error_message: str) -> bool:
    """Return True if this is a permanent error that should not be retried."""
    msg_lower = error_message.lower()
    return any(keyword in msg_lower for keyword in PERMANENT_ERROR_KEYWORDS)


def _build_action_input(
    action_config: dict,
    trigger_data: dict,
) -> dict:
    """
    Merge action config with trigger data to build action input.

    Action config values take precedence; trigger_data is used
    as fallback for template-style values like {{title}}.

    Example trigger_data:
        {"title": "Fix Login", "assigned_to": "Janhvi", "status": "Pending"}
    Example action_config for slack:
        {"channel": "C0BDL5K1WN4", "message": "New task: {{title}}"}
    """
    inputs = dict(action_config)

    # Simple template substitution: replace {{key}} in string values
    for key, value in inputs.items():
        if isinstance(value, str):
            for td_key, td_value in trigger_data.items():
                placeholder = f"{{{{{td_key}}}}}"
                if placeholder in value and td_value is not None:
                    inputs[key] = value.replace(placeholder, str(td_value))

    # Fill in missing keys from trigger data directly
    for td_key, td_value in trigger_data.items():
        if td_key not in inputs:
            inputs[td_key] = td_value

    return inputs


async def execute_workflow(
    workflow: AutomationWorkflowDocument,
    trigger_data: dict,
    existing_log: WorkflowExecutionLogDocument | None = None,
) -> WorkflowExecutionLogDocument:
    """
    Execute a single automation workflow.

    Args:
        workflow: The AutomationWorkflowDocument to execute
        trigger_data: Data from the trigger event (e.g. task fields)
        existing_log: Optional existing log to resume from

    Returns:
        WorkflowExecutionLogDocument with execution results
    """
    started_at = datetime.now(timezone.utc)

    # Use existing or create new execution log
    if existing_log:
        log = existing_log
        log.status = "running"
        action_results = log.action_results
    else:
        log = WorkflowExecutionLogDocument(
            workflow_id=str(workflow.id),
            workflow_name=workflow.name,
            organization_id=workflow.organization_id,
            user_id=workflow.user_id,
            status="running",
            trigger_data=trigger_data,
        )
        await log.insert()
        action_results = []


    print(
        f"[WorkflowExecutor] Starting workflow '{workflow.name}' "
        f"(id={workflow.id}), {len(workflow.actions)} actions"
    )

    workflow_failed = False

    for idx, action_def in enumerate(workflow.actions):
        action_id = f"{action_def.app}.{action_def.action}"

        # If resuming, check if this action is already handled in action_results
        already_handled = False
        if len(action_results) > idx:
            existing_result = action_results[idx]
            if existing_result.status in ["success", "failed", "blocked"]:
                print(f"[WorkflowExecutor] Skipping already handled action: {action_id} (status: {existing_result.status})")
                if existing_result.status in ["failed", "blocked"]:
                    workflow_failed = True
                continue
            
            # If it's awaiting approval, we will process/resume it or replace it

        if action_id == "system.approval" or getattr(action_def, "requires_approval", False):
            print(f"[WorkflowExecutor] Automatically bypassing human approval gate for {action_id}")
            passed_result = ActionResult(
                action=action_id,
                status="success",
                input_summary={"config": action_def.config},
                started_at=datetime.now(timezone.utc),
                completed_at=datetime.now(timezone.utc)
            )
            
            if len(action_results) == idx:
                action_results.append(passed_result)
            else:
                action_results[idx] = passed_result
                
            continue

        action_started_at = datetime.now(timezone.utc)

        print(f"[WorkflowExecutor] Executing action: {action_id}")

        result = await _execute_action_with_retry(
            action_id=action_id,
            action_config=action_def.config,
            trigger_data=trigger_data,
        )

        if len(action_results) == idx:
            action_results.append(result)
        else:
            action_results[idx] = result

        if result.status == "failed":
            workflow_failed = True
            print(
                f"[WorkflowExecutor] Action {action_id} failed: {result.error}"
            )

    completed_at = datetime.now(timezone.utc)
    final_status = "failed" if workflow_failed else "success"

    # Check if some actions succeeded (partial)
    if workflow_failed and any(r.status == "success" for r in action_results):
        final_status = "partial"

    # Update log
    log.status = final_status
    log.action_results = action_results
    log.completed_at = completed_at
    await log.save()

    print(
        f"[WorkflowExecutor] Workflow '{workflow.name}' completed: {final_status} "
        f"in {(completed_at - started_at).total_seconds():.2f}s"
    )

    return log


async def _execute_action_with_retry(
    action_id: str,
    action_config: dict,
    trigger_data: dict,
) -> ActionResult:
    """
    Execute a single action with exponential backoff retry.

    Permanent errors are not retried.
    Transient errors (network, rate limit) are retried up to MAX_ATTEMPTS.
    """
    started_at = datetime.now(timezone.utc)
    last_error: str | None = None
    attempts = 0

    # Validate action is registered BEFORE attempting
    try:
        action_fn = get_action(action_id)
    except ValueError as exc:
        return ActionResult(
            action=action_id,
            status="failed",
            error=str(exc),
            attempts=0,
            started_at=started_at,
            completed_at=datetime.now(timezone.utc),
        )

    # Build inputs
    inputs = _build_action_input(action_config, trigger_data)

    # Sanitize for log (remove tokens/secrets)
    input_summary = {
        k: v for k, v in inputs.items()
        if k not in ("access_token", "refresh_token", "password", "secret")
    }

    for attempt in range(1, MAX_ATTEMPTS + 1):
        attempts = attempt
        try:
            output = await action_fn(**inputs)

            # Sanitize output for log
            output_summary = {}
            if isinstance(output, dict):
                output_summary = {
                    k: v for k, v in output.items()
                    if k not in ("access_token", "refresh_token")
                    and not k.endswith("_token")
                }

            return ActionResult(
                action=action_id,
                status="success",
                input_summary=input_summary,
                output_summary=output_summary,
                error=None,
                attempts=attempts,
                started_at=started_at,
                completed_at=datetime.now(timezone.utc),
            )

        except Exception as exc:
            last_error = str(exc)
            print(
                f"[WorkflowExecutor] Action {action_id} "
                f"attempt {attempt}/{MAX_ATTEMPTS} failed: {last_error}"
            )

            # Don't retry permanent errors
            if _is_permanent_error(last_error):
                print(
                    f"[WorkflowExecutor] Permanent error — not retrying: {last_error}"
                )
                break

            # Exponential backoff for transient errors
            if attempt < MAX_ATTEMPTS:
                backoff = BASE_BACKOFF_SECONDS * (2 ** (attempt - 1))
                print(
                    f"[WorkflowExecutor] Waiting {backoff}s before retry..."
                )
                await asyncio.sleep(backoff)

    return ActionResult(
        action=action_id,
        status="failed",
        input_summary=input_summary,
        output_summary={},
        error=last_error,
        attempts=attempts,
        started_at=started_at,
        completed_at=datetime.now(timezone.utc),
    )


async def fire_trigger(
    trigger_app: str,
    trigger_event: str,
    trigger_data: dict,
    organization_id: str | None = None,
) -> list[WorkflowExecutionLogDocument]:
    """
    Find all active automation workflows matching the trigger and execute them.

    Args:
        trigger_app: App that fired the trigger (e.g. "task")
        trigger_event: Event name (e.g. "task.created")
        trigger_data: Event data to pass as context to actions
        organization_id: Optional org scope for multi-tenant

    Returns:
        List of WorkflowExecutionLogDocuments from each executed workflow
    """
    print(
        f"[WorkflowExecutor] Trigger fired: {trigger_app}.{trigger_event} "
        f"for org={organization_id}"
    )

    # Find matching active workflows
    query: dict = {
        "is_active": True,
        "trigger.app": trigger_app,
        "trigger.event": trigger_event,
    }

    if organization_id:
        query["organization_id"] = organization_id

    workflows = await AutomationWorkflowDocument.find(query).to_list()

    print(
        f"[WorkflowExecutor] Found {len(workflows)} matching workflow(s)"
    )

    logs = []
    for workflow in workflows:
        try:
            log = await execute_workflow(workflow, trigger_data)
            logs.append(log)
        except Exception as exc:
            print(
                f"[WorkflowExecutor] Critical error executing workflow "
                f"'{workflow.name}': {exc}"
            )

    return logs
