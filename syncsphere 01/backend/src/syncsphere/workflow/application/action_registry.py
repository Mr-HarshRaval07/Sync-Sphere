"""
Action Registry

Central mapping from string action identifiers to their implementation functions.
Used by the workflow executor to dispatch actions.

ONLY actions registered here can be executed by automation workflows.
This prevents arbitrary code execution from AI-generated workflows.
"""

from syncsphere.connectors.presentation.google_gmail import send_gmail_email
from syncsphere.connectors.presentation.google_calendar import create_google_calendar_event
from syncsphere.connectors.presentation.google_sheets import append_google_sheet_row
from syncsphere.connectors.presentation.github_actions import create_github_issue
from syncsphere.connectors.presentation.slack_actions import send_slack_message

# Centralized Capability Registry containing display metadata, connection requirements,
# and parameter input validation schemas. Consumed by both the AI Planner and Frontend.
CAPABILITY_REGISTRY: dict = {
    "gmail": {
        "app": "gmail",
        "display_name": "Google Gmail",
        "actions": {
            "send_email": {
                "action": "send_email",
                "display_name": "Send Email",
                "description": "Send an email to a recipient",
                "required_fields": ["to", "subject", "body"],
                "input_schema": {
                    "to": {"type": "string", "description": "Recipient email address"},
                    "subject": {"type": "string", "description": "Subject of the email"},
                    "body": {"type": "string", "description": "Plain text or HTML email body"}
                }
            }
        }
    },
    "google_calendar": {
        "app": "google_calendar",
        "display_name": "Google Calendar",
        "actions": {
            "create_event": {
                "action": "create_event",
                "display_name": "Create Event",
                "description": "Create a meeting or event in Google Calendar",
                "required_fields": ["summary", "start_datetime", "end_datetime"],
                "input_schema": {
                    "summary": {"type": "string", "description": "Event summary or title"},
                    "description": {"type": "string", "description": "Event description text"},
                    "start_datetime": {"type": "string", "description": "Start datetime in ISO-8601 formatting"},
                    "end_datetime": {"type": "string", "description": "End datetime in ISO-8601 formatting"},
                    "timezone": {"type": "string", "description": "Timezone name, defaults to UTC"}
                }
            }
        }
    },
    "google_sheets": {
        "app": "google_sheets",
        "display_name": "Google Sheets",
        "actions": {
            "append_row": {
                "action": "append_row",
                "display_name": "Append Row",
                "description": "Append a row of data to a spreadsheet",
                "required_fields": ["spreadsheet_id", "range_name", "values"],
                "input_schema": {
                    "spreadsheet_id": {"type": "string", "description": "Target Google Spreadsheet ID"},
                    "range_name": {"type": "string", "description": "Range destination, e.g. Sheet1!A1"},
                    "values": {"type": "array", "description": "Row cells list of values to write"}
                }
            }
        }
    },
    "github": {
        "app": "github",
        "display_name": "GitHub Issues",
        "actions": {
            "create_issue": {
                "action": "create_issue",
                "display_name": "Create Issue",
                "description": "Create an issue in a GitHub repository",
                "required_fields": ["owner", "repo", "title", "body"],
                "input_schema": {
                    "owner": {"type": "string", "description": "Owner repository organization username"},
                    "repo": {"type": "string", "description": "Target repository project name"},
                    "title": {"type": "string", "description": "Title of the issue"},
                    "body": {"type": "string", "description": "Body summary text of the issue"}
                }
            }
        }
    },
    "slack": {
        "app": "slack",
        "display_name": "Slack Notification",
        "actions": {
            "send_message": {
                "action": "send_message",
                "display_name": "Send Message",
                "description": "Post a message or notification in a channel",
                "required_fields": ["channel", "message"],
                "input_schema": {
                    "channel": {"type": "string", "description": "Slack channel identifier or name"},
                    "message": {"type": "string", "description": "Notification content body text"}
                }
            }
        }
    }
}

# Maps string action identifiers to async callable functions.
# Each function must accept **kwargs so the executor can pass
# action config + trigger data dynamically.
ACTION_REGISTRY: dict = {
    # -----------------------------------------------------------------
    # Gmail
    # -----------------------------------------------------------------
    "gmail.send_email": send_gmail_email,

    # -----------------------------------------------------------------
    # Google Calendar
    # -----------------------------------------------------------------
    "google_calendar.create_event": create_google_calendar_event,

    # -----------------------------------------------------------------
    # Google Sheets
    # -----------------------------------------------------------------
    "google_sheets.append_row": append_google_sheet_row,

    # -----------------------------------------------------------------
    # GitHub
    # -----------------------------------------------------------------
    "github.create_issue": create_github_issue,

    # -----------------------------------------------------------------
    # Slack
    # -----------------------------------------------------------------
    "slack.send_message": send_slack_message,
}


def get_action(action_id: str):
    """
    Retrieve an action function by its identifier.
    Raises ValueError if the action is not registered.
    """
    fn = ACTION_REGISTRY.get(action_id)
    if fn is None:
        raise ValueError(
            f"Action '{action_id}' is not registered. "
            f"Available actions: {list(ACTION_REGISTRY.keys())}"
        )
    return fn


def list_available_actions() -> list[str]:
    """Return all registered action identifiers."""
    return list(ACTION_REGISTRY.keys())
