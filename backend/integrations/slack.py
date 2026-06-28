import os
import requests

try:
    from backend.config import SLACK_CHANNEL, SLACK_TOKEN, SLACK_WEBHOOK_URL
except ModuleNotFoundError:
    from config import SLACK_CHANNEL, SLACK_TOKEN, SLACK_WEBHOOK_URL


def send_slack_message(channel: str | None = None, message: str = ""):
    """
    Send a message to a Slack channel using Slack Web API.
    Returns the Slack API JSON response.
    """

    if not message:
        raise ValueError("A message is required")

    target_channel = (channel or SLACK_CHANNEL or os.getenv("SLACK_CHANNEL") or "#all-janhvi").strip()
    token = (SLACK_TOKEN or os.getenv("SLACK_TOKEN") or "").strip()
    webhook_url = (SLACK_WEBHOOK_URL or os.getenv("SLACK_WEBHOOK_URL") or "").strip()

    if webhook_url:
        response = requests.post(
            webhook_url,
            json={"text": message, "channel": target_channel},
            timeout=10,
        )
        result = response.json() if response.headers.get("content-type", "").startswith("application/json") else {"ok": True, "message": "sent"}
        print("Slack Webhook Response:", result)
        return result

    if not token:
        return {
            "ok": False,
            "error": "missing_slack_token",
            "message": "SLACK_TOKEN was not found in the environment"
        }

    url = "https://slack.com/api/chat.postMessage"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    payload = {
        "channel": target_channel,
        "text": message
    }

    response = requests.post(url, headers=headers, json=payload, timeout=10)
    result = response.json()

    if not result.get("ok"):
        result["hint"] = "Invite the Slack app to the channel or add SLACK_WEBHOOK_URL in your environment."

    print("Slack Response:", result)
    return result


def notify_task_created(task_title: str, assigned_to: str, status: str = "Pending"):
    message = f"New task created: {task_title} | Assigned to: {assigned_to} | Status: {status}"
    return send_slack_message(message=message)