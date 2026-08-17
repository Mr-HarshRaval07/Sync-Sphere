"""
Slack Actions Connector — Real Implementation

Sends messages and interacts with Slack using the stored Slack OAuth token.
"""
import httpx

from syncsphere.tasks.documents import SlackTokenDocument


async def _get_slack_token(organization_id: str | None = None, slack_workspace: str | None = None, user_id: str | None = None) -> str:
    """
    Retrieve the stored Slack OAuth access token.
    Falls back to first available token for single-tenant / dev if no workspace requested.
    """
    token_doc: SlackTokenDocument | None = None

    if slack_workspace and organization_id and user_id:
        import re
        token_doc = await SlackTokenDocument.find_one(
            {"team_name": {"$regex": f".*{re.escape(slack_workspace)}.*", "$options": "i"}, "organization_id": organization_id, "user_id": user_id}
        )
        if not token_doc:
            raise RuntimeError(
                f"Requested Slack workspace '{slack_workspace}' is not authorized. "
                "Please connect it at /dashboard/connectors."
            )
    elif organization_id and user_id:
        token_doc = await SlackTokenDocument.find_one(
            {"organization_id": organization_id, "user_id": user_id}
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
    slack_workspace: str | None = None,
    user_id: str | None = None,
    **kwargs,
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
    access_token = await _get_slack_token(organization_id, slack_workspace, user_id)

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    actual_channel = channel

    if not actual_channel:
        raise RuntimeError("Missing required field: channel")
    
    if actual_channel.lower() in ["my channel", "the channel", "slack channel"]:
        raise RuntimeError(f"Invalid placeholder channel specified: '{channel}'. Please specify a real channel ID or name.")

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

        if error == "account_inactive":
            raise RuntimeError(
                "Slack account is inactive or the connected Slack credential is no longer valid. "
                "Please reconnect Slack or verify that the Slack workspace/account is active."
            )

        raise RuntimeError(
            f"Slack API error: {error}. "
            f"Response: {data}"
        )

    print(
        f"[Slack] Message sent to {channel}. "
        f"Timestamp: {data.get('ts')}"
    )
    chan_id = data.get("channel") or actual_channel
    ts = data.get("ts")

    permalink = None
    if chan_id and ts:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                perm_res = await client.get(
                    "https://slack.com/api/chat.getPermalink",
                    headers=headers,
                    params={"channel": chan_id, "message_ts": ts},
                )
                perm_data = perm_res.json()
                if perm_data.get("ok"):
                    permalink = perm_data.get("permalink")
        except Exception:
            pass

    if not permalink and chan_id:
        if ts:
            permalink = f"https://slack.com/app_redirect?channel={chan_id}&message_ts={ts}"
        else:
            permalink = f"https://slack.com/app_redirect?channel={chan_id}"

    data["message_permalink"] = permalink
    data["permalink"] = permalink
    data["slack_link"] = permalink
    data["channel_url"] = f"https://slack.com/app_redirect?channel={chan_id}" if chan_id else None
    return data


async def list_slack_channels(
    organization_id: str | None = None,
    user_id: str | None = None,
    **kwargs,
) -> list:
    """
    List all Slack channels the bot has access to.
    Useful for letting users pick a channel in the UI.
    """
    access_token = await _get_slack_token(organization_id, user_id=user_id)

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
