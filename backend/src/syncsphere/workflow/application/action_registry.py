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
from syncsphere.connectors.presentation.jira_actions import (
    create_issue,
    update_issue,
    add_comment,
    search_issues,
    get_issue
)
from syncsphere.connectors.presentation.notion_actions import (
    create_page as notion_create_page,
    append_block as notion_append_blocks,
    search_pages as notion_search_pages,
    create_database_entry as notion_create_database_item,
    update_page as notion_update_page,
    create_meeting_notes as notion_create_meeting_notes,
    save_ai_summary as notion_save_ai_summary,
    create_knowledge_base as notion_create_knowledge_base_article
)

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
                    "body": {"type": "string", "description": "Plain text or HTML email body"},
                    "google_email": {"type": "string", "description": "Optional explicitly requested SENDER/ACTING Google account. NEVER PUT THE RECIPIENT EMAIL HERE. Only use if user explicitly says 'send using john...' or 'from john...'."}
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
                    "timezone": {"type": "string", "description": "Timezone name, defaults to UTC"},
                    "google_email": {"type": "string", "description": "Optional explicitly requested source Google account/email to use"}
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
                "required_fields": ["range_name", "values"],
                "input_schema": {
                    "spreadsheet_name": {"type": "string", "description": "Optional Target Google Spreadsheet Name or Title"},
                    "spreadsheet_id": {"type": "string", "description": "Optional Target Google Spreadsheet Name or ID"},
                    "range_name": {"type": "string", "description": "Range destination, e.g. Sheet1"},
                    "values": {"type": "array", "description": "Row cells list of values to write"},
                    "google_email": {"type": "string", "description": "Optional explicitly requested source Google account/email to use"}
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
                    "message": {"type": "string", "description": "Notification content body text"},
                    "slack_workspace": {"type": "string", "description": "Optional explicitly requested Slack team or workspace name. ONLY populate if user explicitly asks for a particular workspace."}
                }
            }
        }
    },
    "jira": {
        "app": "jira",
        "display_name": "Atlassian Jira",
        "actions": {
            "create_issue": {
                "action": "create_issue",
                "display_name": "Create Issue",
                "description": "Create a new Jira issue",
                "required_fields": ["project_key", "summary"],
                "input_schema": {
                    "project_key": {"type": "string", "description": "Target Jira project key"},
                    "summary": {"type": "string", "description": "Title/summary of the issue"},
                    "issue_type": {"type": "string", "description": "Type of issue to create (e.g. Task, Bug)"},
                    "description": {"type": "string", "description": "Issue description body"}
                }
            },
            "update_issue": {
                "action": "update_issue",
                "display_name": "Update Issue",
                "description": "Update an existing Jira issue",
                "required_fields": ["issue_key_or_id"],
                "input_schema": {
                    "issue_key_or_id": {"type": "string", "description": "Target Jira issue key or ID"},
                    "summary": {"type": "string", "description": "New title/summary of the issue"},
                    "description": {"type": "string", "description": "New issue description body"}
                }
            },
            "add_comment": {
                "action": "add_comment",
                "display_name": "Add Comment",
                "description": "Add a comment to an existing Jira issue",
                "required_fields": ["issue_key_or_id", "body"],
                "input_schema": {
                    "issue_key_or_id": {"type": "string", "description": "Target Jira issue key or ID"},
                    "body": {"type": "string", "description": "Comment body text"}
                }
            },
            "search_issues": {
                "action": "search_issues",
                "display_name": "Search Issues",
                "description": "Search issues using JQL",
                "required_fields": ["jql"],
                "input_schema": {
                    "jql": {"type": "string", "description": "Jira Query Language (JQL) string"},
                    "max_results": {"type": "integer", "description": "Maximum number of results to return (default 10)"}
                }
            },
            "get_issue": {
                "action": "get_issue",
                "display_name": "Get Issue",
                "description": "Retrieve details of a specific Jira issue",
                "required_fields": ["issue_key_or_id"],
                "input_schema": {
                    "issue_key_or_id": {"type": "string", "description": "Target Jira issue key or ID"}
                }
            }
        }
    },
    "notion": {
        "app": "notion",
        "display_name": "Notion",
        "actions": {
            "create_page": {
                "action": "create_page",
                "display_name": "Create Page",
                "description": "Create a new Notion page, doc, database, meeting notes, or workspace documentation. Use this for ANY notion page or notes creation.",
                "required_fields": ["title","parent_id"],
                "input_schema": {
                    "title": {"type": "string", "description": "Title of the page"},
                    "content": {"type": "string", "description": "Markdown body content"},
                    "parent_id": {"type": "string", "description": "LEAVE THIS BLANK. DO NOT GUESS OR INVENT THIS ID. ALWAYS omit this so the user can select it later. This is the Parent page or database ID."},
                    "parent_type": {"type": "string", "description": "Type of parent ('page' or 'database')"},
                    "icon": {"type": "string", "description": "Emoji or URL for icon"},
                    "cover": {"type": "string", "description": "URL for cover image"}
                }
            },
            "append_blocks": {
                "action": "append_blocks",
                "display_name": "Append Blocks",
                "description": "Append text blocks to an existing page",
                "required_fields": ["page_id"],
                "input_schema": {
                    "page_id": {"type": "string", "description": "Target Notion page ID"},
                    "paragraph": {"type": "string", "description": "Paragraph text"},
                    "checklist": {"type": "string", "description": "Newline separated checklist items"},
                    "heading": {"type": "string", "description": "Heading text"},
                    "bullets": {"type": "string", "description": "Newline separated bullet points"},
                    "code_block": {"type": "string", "description": "Code block content"},
                    "quote": {"type": "string", "description": "Quote text"},
                    "divider": {"type": "boolean", "description": "Append a divider"}
                }
            },
            "search_pages": {
                "action": "search_pages",
                "display_name": "Search Pages",
                "description": "Search Notion for pages or databases",
                "required_fields": ["query"],
                "input_schema": {
                    "query": {"type": "string", "description": "Search query text"}
                }
            },
            "create_database_item": {
                "action": "create_database_item",
                "display_name": "Create Database Item",
                "description": "Create an item inside a Notion database with properties",
                "required_fields": ["database_id", "name"],
                "input_schema": {
                    "database_id": {"type": "string", "description": "Target database ID"},
                    "name": {"type": "string", "description": "Title of the item"},
                    "status": {"type": "string", "description": "Status property"},
                    "priority": {"type": "string", "description": "Priority property"},
                    "due_date": {"type": "string", "description": "Due date ISO string"},
                    "owner": {"type": "string", "description": "Owner name"}
                }
            },
            "update_page": {
                "action": "update_page",
                "display_name": "Update Page",
                "description": "Update or archive a page",
                "required_fields": ["page_id"],
                "input_schema": {
                    "page_id": {"type": "string", "description": "Target page ID"},
                    "title": {"type": "string", "description": "New title"},
                    "content": {"type": "string", "description": "New blocks to append"},
                    "archived": {"type": "boolean", "description": "Archive page"}
                }
            },
            "create_meeting_notes": {
                "action": "create_meeting_notes",
                "display_name": "Create Meeting Notes",
                "description": "Create a new Notion page for meeting notes",
                "required_fields": ["title", "parent_id"],
                "input_schema": {
                    "title": {"type": "string", "description": "Title of the meeting"},
                    "participants": {"type": "string", "description": "Meeting participants list"},
                    "agenda": {"type": "string", "description": "Meeting agenda items"},
                    "summary": {"type": "string", "description": "Meeting summary"},
                    "action_items": {"type": "string", "description": "Action items from the meeting"},
                    "next_meeting": {"type": "string", "description": "Date or details for the next meeting"},
                    "parent_id": {"type": "string", "description": "LEAVE THIS BLANK. DO NOT GUESS OR INVENT THIS ID. ALWAYS omit this so the user can select it later. Parent Page ID"}
                }
            },
            "save_ai_summary": {
                "action": "save_ai_summary",
                "display_name": "Save AI Summary",
                "description": "Save an AI generated summary to Notion",
                "required_fields": ["title", "parent_id"],
                "input_schema": {
                    "title": {"type": "string", "description": "Summary title"},
                    "content": {"type": "string", "description": "Summary content"},
                    "parent_id": {"type": "string", "description": "LEAVE THIS BLANK. DO NOT GUESS OR INVENT THIS ID. ALWAYS omit this so the user can select it later. Parent ID"}
                }
            },
            "create_knowledge_base_article": {
                "action": "create_knowledge_base_article",
                "display_name": "Create KB Article",
                "description": "Create a comprehensive knowledge base article/documentation",
                "required_fields": ["title", "parent_id"],
                "input_schema": {
                    "title": {"type": "string", "description": "Article title"},
                    "description": {"type": "string", "description": "High level description"},
                    "steps": {"type": "string", "description": "Step by step usage"},
                    "references": {"type": "string", "description": "Reference URLs"},
                    "tags": {"type": "string", "description": "Comma separated tags"},
                    "parent_id": {"type": "string", "description": "LEAVE THIS BLANK. DO NOT GUESS OR INVENT THIS ID. ALWAYS omit this so the user can select it later. Parent ID"}
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

    # -----------------------------------------------------------------
    # Jira
    # -----------------------------------------------------------------
    "jira.create_issue": create_issue,
    "jira.update_issue": update_issue,
    "jira.add_comment": add_comment,
    "jira.search_issues": search_issues,
    "jira.get_issue": get_issue,

    # -----------------------------------------------------------------
    # Notion
    # -----------------------------------------------------------------
    "notion.create_page": notion_create_page,
    "notion.append_blocks": notion_append_blocks,
    "notion.search_pages": notion_search_pages,
    "notion.create_database_item": notion_create_database_item,
    "notion.update_page": notion_update_page,
    "notion.create_meeting_notes": notion_create_meeting_notes,
    "notion.save_ai_summary": notion_save_ai_summary,
    "notion.create_knowledge_base_article": notion_create_knowledge_base_article,
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
