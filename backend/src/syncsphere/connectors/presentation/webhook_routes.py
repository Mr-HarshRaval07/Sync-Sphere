"""
Webhook Routes

Handles incoming webhook events from GitHub and Slack.

Both endpoints:
1. Verify the request signature (security)
2. Parse the event
3. Find matching active automation workflows
4. Execute workflows asynchronously

POST /v1/webhooks/github  — GitHub events (issue.created, PR, etc.)
POST /v1/webhooks/slack   — Slack Events API
"""
import hashlib
import hmac
import json
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Header, HTTPException, Request
from fastapi.responses import JSONResponse

from syncsphere.core.config.settings import settings

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


# ---------------------------------------------------------------------------
# GitHub Webhook
# ---------------------------------------------------------------------------

async def _verify_github_signature(
    raw_body: bytes,
    signature_header: str | None,
) -> None:
    """
    Verify GitHub webhook signature using HMAC-SHA256.
    GitHub sends: X-Hub-Signature-256: sha256=<hex_digest>
    """
    webhook_secret = getattr(settings, "github_webhook_secret", None)

    if not webhook_secret:
        # If no webhook secret configured, skip verification (dev mode)
        print("[Webhooks] WARNING: GITHUB_WEBHOOK_SECRET not set — skipping signature verification")
        return

    if not signature_header:
        raise HTTPException(status_code=401, detail="Missing X-Hub-Signature-256 header")

    if not signature_header.startswith("sha256="):
        raise HTTPException(status_code=401, detail="Invalid signature format")

    expected_sig = "sha256=" + hmac.new(
        webhook_secret.encode("utf-8"),
        raw_body,
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(expected_sig, signature_header):
        raise HTTPException(status_code=401, detail="GitHub webhook signature mismatch")


async def _process_github_webhook(event_type: str, payload: dict) -> None:
    """Process a verified GitHub webhook event and fire matching workflows."""
    from syncsphere.workflow.application.workflow_executor import fire_trigger

    event_map = {
        "issues": {
            "opened": "github.issue.created",
            "closed": "github.issue.closed",
            "reopened": "github.issue.reopened",
        },
        "pull_request": {
            "opened": "github.pull_request.created",
            "closed": "github.pull_request.closed",
            "merged": "github.pull_request.merged",
        },
        "push": {
            None: "github.push",
        },
    }

    action = payload.get("action")
    event_id = event_map.get(event_type, {}).get(action) or event_map.get(event_type, {}).get(None)

    if not event_id:
        print(f"[GitHub Webhook] Unhandled event: {event_type}.{action}")
        return

    trigger_data: dict = {
        "event_type": event_type,
        "action": action,
    }

    # Extract useful data from the payload
    if event_type == "issues":
        issue = payload.get("issue", {})
        trigger_data.update({
            "issue_number": issue.get("number"),
            "title": issue.get("title", ""),
            "body": issue.get("body", ""),
            "html_url": issue.get("html_url", ""),
            "repo": payload.get("repository", {}).get("name", ""),
            "owner": payload.get("repository", {}).get("owner", {}).get("login", ""),
            "slack_message": (
                f"🐛 *New GitHub Issue*\n\n"
                f"*#{issue.get('number', '')}:* {issue.get('title', '')}\n"
                f"{issue.get('html_url', '')}"
            ),
            "email_subject": f"New GitHub Issue: {issue.get('title', '')}",
            "email_body": (
                f"A new GitHub issue was created.\n\n"
                f"Issue: #{issue.get('number', '')} — {issue.get('title', '')}\n"
                f"URL: {issue.get('html_url', '')}\n\n"
                f"{issue.get('body', '')}"
            ),
        })

    elif event_type == "pull_request":
        pr = payload.get("pull_request", {})
        trigger_data.update({
            "pr_number": pr.get("number"),
            "title": pr.get("title", ""),
            "html_url": pr.get("html_url", ""),
            "repo": payload.get("repository", {}).get("name", ""),
            "slack_message": (
                f"🔀 *New Pull Request*\n\n"
                f"*#{pr.get('number', '')}:* {pr.get('title', '')}\n"
                f"{pr.get('html_url', '')}"
            ),
        })

    print(f"[GitHub Webhook] Firing trigger: {event_id}")
    await fire_trigger(
        trigger_app="github",
        trigger_event=event_id,
        trigger_data=trigger_data,
    )


@router.post("/github")
async def github_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_hub_signature_256: str | None = Header(default=None),
    x_github_event: str | None = Header(default=None),
):
    """
    Receive GitHub webhook events.

    Configure in GitHub repo Settings → Webhooks:
    - Payload URL: http://your-domain/v1/webhooks/github
    - Content type: application/json
    - Secret: your GITHUB_WEBHOOK_SECRET
    - Events: Issues, Pull requests, Pushes
    """
    raw_body = await request.body()

    # Verify signature
    await _verify_github_signature(raw_body, x_hub_signature_256)

    # Parse payload
    try:
        payload = json.loads(raw_body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    event_type = x_github_event or "unknown"
    print(f"[GitHub Webhook] Received event: {event_type}")

    # Process asynchronously
    background_tasks.add_task(
        _process_github_webhook,
        event_type,
        payload,
    )

    # GitHub expects a 200-level response quickly
    return JSONResponse(
        content={"received": True, "event": event_type},
        status_code=200,
    )


# ---------------------------------------------------------------------------
# Slack Webhook (Events API)
# ---------------------------------------------------------------------------

async def _verify_slack_signature(
    raw_body: bytes,
    timestamp: str | None,
    signature: str | None,
) -> None:
    """
    Verify Slack webhook signature.
    Slack sends: X-Slack-Signature: v0=<hex_digest>
    """
    signing_secret = getattr(settings, "slack_signing_secret", None)

    if not signing_secret:
        print("[Webhooks] WARNING: SLACK_SIGNING_SECRET not set — skipping verification")
        return

    if not timestamp or not signature:
        raise HTTPException(status_code=401, detail="Missing Slack signature headers")

    sig_basestring = f"v0:{timestamp}:{raw_body.decode('utf-8')}"

    expected_sig = "v0=" + hmac.new(
        signing_secret.encode("utf-8"),
        sig_basestring.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(expected_sig, signature):
        raise HTTPException(status_code=401, detail="Slack request signature mismatch")


async def _process_slack_event(payload: dict) -> None:
    """Process a verified Slack event and fire matching workflows."""
    from syncsphere.workflow.application.workflow_executor import fire_trigger

    event = payload.get("event", {})
    event_type = event.get("type", "")

    event_map = {
        "message": "slack.message.received",
    }

    trigger_event = event_map.get(event_type)
    if not trigger_event:
        print(f"[Slack Webhook] Unhandled event type: {event_type}")
        return

    trigger_data = {
        "event_type": event_type,
        "channel": event.get("channel", ""),
        "user": event.get("user", ""),
        "text": event.get("text", ""),
        "ts": event.get("ts", ""),
    }

    await fire_trigger(
        trigger_app="slack",
        trigger_event=trigger_event,
        trigger_data=trigger_data,
    )


@router.post("/slack")
async def slack_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_slack_signature: str | None = Header(default=None),
    x_slack_request_timestamp: str | None = Header(default=None),
):
    """
    Receive Slack Events API events.

    Configure in Slack App settings → Event Subscriptions:
    - Request URL: http://your-domain/v1/webhooks/slack
    - Subscribe to bot events: message.channels
    """
    raw_body = await request.body()

    # Verify signature
    await _verify_slack_signature(raw_body, x_slack_request_timestamp, x_slack_signature)

    try:
        payload = json.loads(raw_body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    # Slack URL verification challenge
    if payload.get("type") == "url_verification":
        return JSONResponse(content={"challenge": payload.get("challenge")})

    event_type = payload.get("type", "")
    print(f"[Slack Webhook] Received event: {event_type}")

    if event_type == "event_callback":
        background_tasks.add_task(_process_slack_event, payload)

    return JSONResponse(content={"ok": True})
