"""
Slack Actions Connector — Real Implementation

Sends messages and interacts with Slack using the stored Slack OAuth token.
"""
import httpx

from syncsphere.tasks.documents import SlackTokenDocument


async def _get_slack_token(organization_id: str | None = None) -> str:
    """
    Retrieve the stored Slack OAuth access token.
    Falls back to first available token for single-tenant / dev.
    """
    token_doc: SlackTokenDocument | None = None

    if organization_id:
        token_doc = await SlackTokenDocument.find_one(
            {"organization_id": organization_id}
        )

    if not token_doc:
        raise RuntimeError(
            "No Slack workspace connected. "
            "Please connect Slack at /dashboard/connectors."
        )

    return token_doc.access_token


async def send_slack_message(
    message: str,
    channel: str | None = None,
    organization_id: str | None = None,
) -> dict:
    """
    Send a message to a Slack channel or user.

    Args:
        message: Message text (Slack mrkdwn format supported)
        channel: Channel ID (e.g. "C0BDL5K1WN4") or channel name (e.g. "#all-janhvi"). Will fallback if None or #general.
        organization_id: Optional org scope for multi-tenant

    Returns:
        Slack API response dict

    Raises:
        RuntimeError: If no Slack token or API call fails
    """
    access_token = await _get_slack_token(organization_id)

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    actual_channel = channel

    if not actual_channel or actual_channel.lower() == "#general":
        # Fallback to the first available channel to prevent automation failure
        channels = await list_slack_channels(organization_id)
        if channels:
            actual_channel = channels[0]["id"]
        else:
            raise RuntimeError("No Slack channels available for this workspace.")

    payload = {
        "channel": actual_channel,
        "text": message,
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.post(
            "https://slack.com/api/chat.postMessage",
            headers=headers,
            json=payload,
        )

    data = response.json()

    if not data.get("ok"):
        error = data.get("error", "unknown_error")

        if error == "not_in_channel":
            raise RuntimeError(
                f"SyncSphere bot is not in channel '{channel}'. "
                "Please invite the bot: /invite @SyncSphere"
            )

        if error == "channel_not_found":
            raise RuntimeError(
                f"Slack channel not found: '{channel}'. "
                "Check the channel ID or name."
            )

        if error == "token_revoked":
            raise RuntimeError(
                "Slack token has been revoked. "
                "Please reconnect Slack at /dashboard/connectors."
            )

        raise RuntimeError(
            f"Slack API error: {error}. "
            f"Response: {data}"
        )

    print(
        f"[Slack] Message sent to {channel}. "
        f"Timestamp: {data.get('ts')}"
    )
    return data


async def list_slack_channels(
    organization_id: str | None = None,
) -> list:
    """
    List all Slack channels the bot has access to.
    Useful for letting users pick a channel in the UI.
    """
    access_token = await _get_slack_token(organization_id)

    headers = {
        "Authorization": f"Bearer {access_token}",
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(
            "https://slack.com/api/conversations.list",
            headers=headers,
            params={"types": "public_channel,private_channel", "limit": 200},
        )

    data = response.json()

    if not data.get("ok"):
        raise RuntimeError(
            f"Slack API failed to list channels: {data.get('error')}"
        )

    return data.get("channels", [])
