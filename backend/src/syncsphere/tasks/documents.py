from typing import Optional, List
from datetime import datetime

from pydantic import Field, BaseModel
from beanie import Document

from syncsphere.shared_kernel.infrastructure.mongodb.base_document import (
    BaseTenantDocument,
)


class TaskAutomation(BaseModel):
    action: str = Field(..., description="Action ID, e.g. slack.send_message")
    config: dict = Field(default_factory=dict, description="Configuration parameters for the action")
    status: str = Field(default="pending", description="pending | success | failed")
    error: Optional[str] = Field(default=None, description="Error message if execution failed")
    requires_approval: bool = Field(default=False, description="Whether this automation explicitly requires human approval before executing")
    executed_at: Optional[datetime] = Field(default=None, description="Datetime when the action was executed")
    result: Optional[dict] = Field(default=None, description="Result output of the action execution")


class TaskDocument(BaseTenantDocument):
    """Beanie ODM document representing a SyncSphere Task."""

    title: str = Field(
        ...,
        description="Task title",
    )

    created_by_user_id: Optional[str] = Field(
        default=None,
        description="User ID of the human who initiated this task",
    )

    description: str = Field(
        default="",
        description="Task description",
    )

    assigned_to: str = Field(
        default="",
        description="User or name assigned to the task",
    )

    priority: str = Field(
        default="Medium",
        description="High | Medium | Low",
    )

    status: str = Field(
        default="Pending",
        description="Pending | In Progress | Completed",
    )

    due_date: Optional[str] = Field(
        default=None,
        description="Due date as ISO string or human-readable",
    )

    automations: List[TaskAutomation] = Field(
        default_factory=list,
        description="Optional automation steps executed when task is created/run",
    )

    class Settings:
        name = "tasks"

        indexes = [
            "org_id",
            ("org_id", "status"),
            ("org_id", "priority"),
        ]


# ---------------------------------------------------------------------------
# Slack Token
# ---------------------------------------------------------------------------

class SlackTokenDocument(Document):
    """
    Stores the Slack bot OAuth token per workspace.
    team_id is used to identify the Slack workspace.
    """

    team_id: str = Field(
        ...,
        description="Slack team/workspace ID (used as unique key)",
    )

    user_id: Optional[str] = Field(
        default=None,
        description="SyncSphere user ID",
    )

    organization_id: Optional[str] = Field(
        default=None,
        description="SyncSphere organization ID",
    )

    team_name: str = Field(
        default="",
        description="Slack workspace name",
    )

    access_token: str = Field(
        ...,
        description="Slack bot access token (xoxb-...)",
    )

    created_at: datetime = Field(
        default_factory=datetime.utcnow,
    )

    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
    )

    async def save(self, *args, **kwargs):
        self.updated_at = datetime.utcnow()
        return await super().save(*args, **kwargs)

    class Settings:
        name = "slack_tokens"
        indexes = ["team_id", "organization_id", "user_id"]


# ---------------------------------------------------------------------------
# Google Token
# ---------------------------------------------------------------------------

class GoogleTokenDocument(Document):
    """
    Stores Google OAuth credentials for a connected Google account.

    One Google OAuth connection provides access to:
    - Gmail
    - Google Calendar
    - Google Sheets
    """

    user_id: Optional[str] = Field(
        default=None,
        description="SyncSphere user ID",
    )

    organization_id: Optional[str] = Field(
        default=None,
        description="SyncSphere organization ID",
    )

    google_email: Optional[str] = Field(
        default=None,
        description="Google account email address",
    )

    access_token: str = Field(
        ...,
        description="Current Google OAuth access token",
    )

    refresh_token: str = Field(
        ...,
        description="Google OAuth refresh token",
    )

    token_expiry: Optional[float] = Field(
        default=None,
        description="Access token expiry as Unix timestamp",
    )

    scopes: List[str] = Field(
        default_factory=list,
        description="Google OAuth scopes granted to SyncSphere",
    )

    created_at: datetime = Field(
        default_factory=datetime.utcnow,
    )

    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
    )

    async def save(self, *args, **kwargs):
        self.updated_at = datetime.utcnow()
        return await super().save(*args, **kwargs)

    class Settings:
        name = "google_tokens"
        indexes = [
            "user_id",
            "organization_id",
            "google_email",
        ]


# ---------------------------------------------------------------------------
# GitHub Token
# ---------------------------------------------------------------------------

class GitHubTokenDocument(Document):
    """
    Stores GitHub OAuth token per connected GitHub account.
    Saved after user completes GitHub OAuth flow.
    """

    user_id: Optional[str] = Field(
        default=None,
        description="SyncSphere user ID",
    )

    organization_id: Optional[str] = Field(
        default=None,
        description="SyncSphere organization ID",
    )

    github_username: str = Field(
        ...,
        description="GitHub username (login)",
    )

    github_user_id: int = Field(
        default=0,
        description="GitHub numeric user ID",
    )

    access_token: str = Field(
        ...,
        description="GitHub OAuth access token",
    )

    scopes: List[str] = Field(
        default_factory=list,
        description="GitHub OAuth scopes",
    )

    created_at: datetime = Field(
        default_factory=datetime.utcnow,
    )

    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
    )

    async def save(self, *args, **kwargs):
        self.updated_at = datetime.utcnow()
        return await super().save(*args, **kwargs)

    class Settings:
        name = "github_tokens"
        indexes = [
            "user_id",
            "github_username",
        ]


# ---------------------------------------------------------------------------
# Notion Token
# ---------------------------------------------------------------------------

class AccessiblePage(BaseModel):
    id: str
    title: str
    type: str

class NotionTokenDocument(Document):
    """
    Stores Notion OAuth credentials per workspace connection.
    """

    user_id: Optional[str] = Field(
        default=None,
        description="SyncSphere user ID",
    )

    organization_id: Optional[str] = Field(
        default=None,
        description="SyncSphere organization ID",
    )

    workspace_id: str = Field(
        ...,
        description="Notion workspace ID",
    )

    workspace_name: Optional[str] = Field(
        default=None,
        description="Workspace name",
    )
    
    workspace_icon: Optional[str] = Field(
        default=None,
        description="Workspace icon url",
    )

    access_token: str = Field(
        ...,
        description="Notion bot access token",
    )

    bot_id: str = Field(
        ...,
        description="Notion bot ID",
    )
    
    owner: str = Field(
        ...,
        description="Notion connection owner ID (user)",
    )
    
    duplicated_template_id: Optional[str] = Field(
        default=None,
    )
    
    token_type: Optional[str] = Field(
        default=None,
    )
    
    default_parent_id: Optional[str] = Field(
        default=None,
        description="The default parent page or database ID configured by the user."
    )
    
    default_parent_type: Optional[str] = Field(
        default=None,
        description="The type of the default parent ('page' or 'database')."
    )

    accessible_pages: List[AccessiblePage] = Field(
        default_factory=list,
        description="Cached list of accessible Notion pages and databases loaded during OAuth flow",
    )

    created_at: datetime = Field(
        default_factory=datetime.utcnow,
    )

    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
    )

    async def save(self, *args, **kwargs):
        self.updated_at = datetime.utcnow()
        return await super().save(*args, **kwargs)

    class Settings:
        name = "notion_tokens"
        indexes = [
            "organization_id",
            "user_id",
            "workspace_id",
        ]


# ---------------------------------------------------------------------------
# OAuth State
# ---------------------------------------------------------------------------
class OAuthStateDocument(Document):
    """
    Temporary server-side state record for secure OAuth context passing
    without placing JWT tokens in the redirect URLs.
    """
    
    state: str = Field(..., description="Unique state generated for the OAuth flow")
    provider: str = Field(..., description="google | slack | github")
    user_id: Optional[str] = Field(default=None, description="SyncSphere user ID")
    organization_id: Optional[str] = Field(default=None, description="SyncSphere organization ID")
    requested_account: Optional[str] = Field(default=None, description="Explicit account constraint")
    expires_at: datetime = Field(..., description="Expiration timestamp for this state")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "oauth_states"
        indexes = ["state", "expires_at"]


# ---------------------------------------------------------------------------
# Automation Workflow (Zapier-like trigger + actions)
# Separate from the existing DAG-based WorkflowDocument in workflow/
# ---------------------------------------------------------------------------

class AutomationTrigger(BaseModel):
    """Defines what event starts the automation."""
    app: str = Field(
        ...,
        description="App that triggers the workflow: task, github, slack",
    )
    event: str = Field(
        ...,
        description="Event name: task.created, issue.created, etc.",
    )


class AutomationAction(BaseModel):
    """Defines a single action to execute in the automation."""
    app: str = Field(
        ...,
        description="App to call: gmail, slack, google_sheets, github",
    )
    action: str = Field(
        ...,
        description="Action to perform: send_email, send_message, append_row, create_issue",
    )
    config: dict = Field(
        default_factory=dict,
        description="Default configuration values for this action (e.g. channel, spreadsheet_id)",
    )
    requires_approval: bool = Field(
        default=False,
        description="Whether this action explicitly requires human approval before executing",
    )


class AutomationWorkflowDocument(Document):
    """
    Zapier-like automation workflow document.

    Each workflow has:
    - A trigger (what event starts it)
    - A list of actions (what to do when triggered)

    This is SEPARATE from the existing DAG-based WorkflowDocument
    which is used for multi-agent AI orchestration.
    """

    name: str = Field(
        ...,
        description="Human-readable workflow name",
    )

    user_id: Optional[str] = Field(
        default=None,
        description="SyncSphere user who created this workflow",
    )

    organization_id: Optional[str] = Field(
        default=None,
        description="SyncSphere organization this workflow belongs to",
    )

    is_active: bool = Field(
        default=True,
        description="Whether this workflow is currently active",
    )

    trigger: AutomationTrigger = Field(
        ...,
        description="Trigger that starts this workflow",
    )

    actions: List[AutomationAction] = Field(
        default_factory=list,
        description="Ordered list of actions to execute",
    )

    created_at: datetime = Field(
        default_factory=datetime.utcnow,
    )

    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
    )

    async def save(self, *args, **kwargs):
        self.updated_at = datetime.utcnow()
        return await super().save(*args, **kwargs)

    class Settings:
        name = "automation_workflows"
        indexes = [
            "organization_id",
            ("organization_id", "is_active"),
            "user_id",
        ]


# ---------------------------------------------------------------------------
# Workflow Execution Log
# ---------------------------------------------------------------------------

class ActionResult(BaseModel):
    """Records the result of a single action execution."""
    action: str = Field(..., description="Action identifier e.g. gmail.send_email")
    status: str = Field(..., description="success | failed | skipped")
    input_summary: dict = Field(
        default_factory=dict,
        description="Sanitized summary of inputs (NO tokens or secrets)",
    )
    output_summary: dict = Field(
        default_factory=dict,
        description="Sanitized summary of outputs",
    )
    error: Optional[str] = Field(
        default=None,
        description="Error message if action failed",
    )
    attempts: int = Field(
        default=1,
        description="Number of attempts made",
    )
    started_at: datetime = Field(
        default_factory=datetime.utcnow,
    )
    completed_at: datetime = Field(
        default_factory=datetime.utcnow,
    )
    http_metadata: Optional[dict] = Field(
        default=None,
        description="Detailed HTTP trace: request, response payloads, status code, latency",
    )
    resource_links: Optional[dict] = Field(
        default=None,
        description="Created resource URIs (e.g. Jira issue link, Notion page link)",
    )


class WorkflowExecutionLogDocument(Document):
    """
    Records the complete execution of an automation workflow.
    Used for audit trail and debugging.
    """

    workflow_id: str = Field(
        ...,
        description="ID of the AutomationWorkflowDocument",
    )

    workflow_name: str = Field(
        default="",
        description="Snapshot of workflow name at execution time",
    )

    user_id: Optional[str] = Field(
        default=None,
    )

    organization_id: Optional[str] = Field(
        default=None,
    )
    
    trigger_type: str = Field(
        default="Manual",
        description="Trigger type: Manual, Schedule, Webhook, API, Event",
    )
    
    schedule_id: Optional[str] = Field(
        default=None,
        description="ID of the triggering schedule, if applicable",
    )
    
    environment: str = Field(
        default="Production",
        description="Execution environment sandbox state",
    )

    status: str = Field(
        default="running",
        description="running | success | failed | partial",
    )

    trigger_data: dict = Field(
        default_factory=dict,
        description="Sanitized trigger payload (NO secrets)",
    )
    
    ai_execution_summary: Optional[dict] = Field(
        default=None,
        description="Summary of AI OpenRouter execution traces and token costs",
    )

    action_results: List[ActionResult] = Field(
        default_factory=list,
        description="Results per action in execution order",
    )

    error: Optional[str] = Field(
        default=None,
        description="Top-level error if workflow itself failed to start",
    )

    started_at: datetime = Field(
        default_factory=datetime.utcnow,
    )

    completed_at: Optional[datetime] = Field(
        default=None,
    )
    
    duration_ms: Optional[float] = Field(
        default=None,
        description="Total duration of the execution flow in milliseconds",
    )

    current_step: Optional[str] = Field(
        default=None,
        description="The currently executing step or last active step ID",
    )

    class Settings:
        name = "workflow_execution_logs"
        indexes = [
            "workflow_id",
            "organization_id",
            "status",
        ]


# ---------------------------------------------------------------------------
# Jira Token
# ---------------------------------------------------------------------------

class JiraTokenDocument(Document):
    """
    Stores Jira OAuth credentials for a connected Jira account.
    Tokens are strictly user-isolated.
    """

    user_id: Optional[str] = Field(
        default=None,
        description="SyncSphere user ID",
    )

    organization_id: Optional[str] = Field(
        default=None,
        description="SyncSphere organization ID",
    )

    access_token: str = Field(
        ...,
        description="Jira OAuth access token",
    )

    refresh_token: Optional[str] = Field(
        default=None,
        description="Jira OAuth refresh token",
    )

    cloud_id: Optional[str] = Field(
        default=None,
        description="Jira Cloud ID",
    )

    site_url: Optional[str] = Field(
        default=None,
        description="Jira Site URL",
    )

    site_name: Optional[str] = Field(
        default=None,
        description="Jira Site Name",
    )
    
    account_id: Optional[str] = Field(
        default=None,
        description="Jira Atlassian Account ID",
    )

    expires_at: Optional[datetime] = Field(
        default=None,
        description="When the access token expires",
    )

    created_at: datetime = Field(
        default_factory=datetime.utcnow,
    )

    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
    )

    async def save(self, *args, **kwargs):
        self.updated_at = datetime.utcnow()
        return await super().save(*args, **kwargs)

    class Settings:
        name = "jira_tokens"
        indexes = ["organization_id", "user_id", "cloud_id"]