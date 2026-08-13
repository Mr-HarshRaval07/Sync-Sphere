"""
Jira Token Service

Provides automatic Jira OAuth access token refresh.
Used by Jira connectors.
"""
from datetime import datetime, timezone, timedelta
import httpx

from syncsphere.tasks.documents import JiraTokenDocument
from syncsphere.core.config.settings import settings
from syncsphere.connectors.application.exceptions import OAuthError

JIRA_TOKEN_URL = "https://auth.atlassian.com/oauth/token"
TOKEN_EXPIRY_BUFFER_SECONDS = 300

async def get_valid_jira_token(
    user_id: str,
    organization_id: str | None = None,
) -> str:
    """
    Return a valid Jira access token, refreshing if expired.

    Lookup priority:
    1. Match by user_id AND organization_id (Tenant scoped)
    2. Match by user_id

    Raises OAuthError if no token is found or refresh fails.
    """
    token_doc: JiraTokenDocument | None = None
    if user_id and organization_id:
        token_doc = await JiraTokenDocument.find_one(
            {"user_id": user_id, "organization_id": organization_id}
        )
    elif user_id:
        token_doc = await JiraTokenDocument.find_one({"user_id": user_id})

    if not token_doc:
        raise OAuthError(
            "Your Jira account is not connected to SyncSphere. Connect Jira before executing this action."
        )

    now_ts = datetime.now(timezone.utc).timestamp()

    if (
        token_doc.expires_at
        and now_ts < (token_doc.expires_at.timestamp() - TOKEN_EXPIRY_BUFFER_SECONDS)
    ):
        return token_doc.access_token

    print(
        f"[JiraTokenService] Access token expired for user {user_id}. Refreshing..."
    )

    if not token_doc.refresh_token:
        raise OAuthError("Jira authorization expired (no refresh token). Please reconnect Jira.")

    async with httpx.AsyncClient(timeout=30.0) as client:
        refresh_response = await client.post(
            JIRA_TOKEN_URL,
            json={
                "grant_type": "refresh_token",
                "client_id": settings.jira_client_id,
                "client_secret": settings.jira_client_secret,
                "refresh_token": token_doc.refresh_token,
            },
        )

    if refresh_response.status_code != 200:
        error_data = {}
        try:
            error_data = refresh_response.json()
        except:
            pass
        error_code = error_data.get("error", "")

        if error_code in ("invalid_grant", "invalid_token"):
            raise OAuthError(
                "Jira refresh token has been revoked. "
                "Please reconnect Jira at /dashboard/connectors."
            )

        raise RuntimeError(
            f"Jira token refresh failed. Status: {refresh_response.status_code}. Response: {refresh_response.text}"
        )

    refreshed = refresh_response.json()
    new_access_token = refreshed.get("access_token")
    new_refresh_token = refreshed.get("refresh_token")
    new_expires_in = refreshed.get("expires_in", 3600)

    if not new_access_token:
        raise RuntimeError("Jira token refresh did not return a new access token.")

    token_doc.access_token = new_access_token
    if new_refresh_token:
        token_doc.refresh_token = new_refresh_token
    
    token_doc.expires_at = datetime.now(timezone.utc) + timedelta(seconds=new_expires_in)
    await token_doc.save()

    return token_doc.access_token

async def get_jira_connection_details(user_id: str, organization_id: str | None = None) -> dict | None:
    token_doc: JiraTokenDocument | None = None
    if user_id and organization_id:
        token_doc = await JiraTokenDocument.find_one(
            {"user_id": user_id, "organization_id": organization_id}
        )
    elif user_id:
        token_doc = await JiraTokenDocument.find_one({"user_id": user_id})
        
    if not token_doc:
        return None
        
    return {
        "cloud_id": token_doc.cloud_id,
        "site_url": token_doc.site_url,
        "site_name": token_doc.site_name,
        "account_id": token_doc.account_id
    }
