import requests

try:
    from backend.config import SLACK_TOKEN
except ModuleNotFoundError:
    from config import SLACK_TOKEN


def send_slack_message(channel: str, message: str):
    """
    Send a message to a Slack channel using Slack Web API
    """

    url = "https://slack.com/api/chat.postMessage"

    headers = {
        "Authorization": f"Bearer {SLACK_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "channel": channel,
        "text": message
    }

    response = requests.post(url, headers=headers, json=payload)

    result = response.json()

    # optional debug
    print("Slack Response:", result)

    return result