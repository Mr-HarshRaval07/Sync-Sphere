"""
Google Token Service

Provides automatic Google OAuth access token refresh.
Used by Gmail, Google Calendar, and Google Sheets connectors.
"""
from datetime import datetime, timezone
import httpx

from syncsphere.tasks.documents import GoogleTokenDocument
from syncsphere.core.config.settings import settings
from syncsphere.connectors.application.exceptions import OAuthError


GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"

# Refresh 5 minutes before actual expiry for safety
TOKEN_EXPIRY_BUFFER_SECONDS = 300


async def get_valid_google_token(
    google_email: str | None = None,
    organization_id: str | None = None,
    user_id: str | None = None,
    required_scopes: list[str] | None = None,
) -> str:
    """
    Return a valid Google access token, refreshing if expired.

    Lookup priority:
    1. Match by google_email (most specific)
    2. Match by organization_id
    3. First available token (fallback for single-tenant / dev)

    Raises RuntimeError if no token is found or refresh fails.
    """
    # Find the token document
    token_doc: GoogleTokenDocument | None = None
    if google_email and organization_id and user_id:
        token_doc = await GoogleTokenDocument.find_one(
            {"google_email": {"$regex": f"^{google_email}$", "$options": "i"}, "organization_id": organization_id, "user_id": user_id}
        )
        if not token_doc:
            from syncsphere.connectors.application.exceptions import OAuthError
            raise OAuthError(
                f"Requested Google account '{google_email}' is not authorized for your user. "
                "Please connect it at /dashboard/connectors."
            )
    elif user_id and organization_id:
        token_doc = await GoogleTokenDocument.find_one(
            {"user_id": user_id, "organization_id": organization_id}
        )
    # Explicitly removed bare organization_id token fetching.
    # We must retrieve Gmail OAuth tokens using the CURRENT SyncSphere user's authenticated user_id,
    # or the explicit google_email requested.

    if not token_doc:
        from syncsphere.connectors.application.exceptions import OAuthError
        raise OAuthError(
            "Gmail authorization required. Connect Gmail before executing this task."
        )

    # Validate scopes dynamically based on integration type
    if required_scopes:
        stored_scopes = token_doc.scopes or []
        missing = [req for req in required_scopes if req not in stored_scopes]
        if missing:
            from syncsphere.connectors.application.exceptions import OAuthError
            raise OAuthError(
                f"Gmail permission denied (Missing Required Scope: {missing[0]}). "
                "Please reconnect Google and grant Gmail send permissions."
            )

    # Check whether the access token is still valid
    now_ts = datetime.now(timezone.utc).timestamp()

    if (
        token_doc.token_expiry
        and now_ts < (token_doc.token_expiry - TOKEN_EXPIRY_BUFFER_SECONDS)
    ):
        # Token is still valid
        return token_doc.access_token

    # Token is expired — refresh it
    print(
        f"[GoogleTokenService] Access token expired for "
        f"{token_doc.google_email}. Refreshing..."
    )

    if not token_doc.refresh_token:
        raise OAuthError(
            "Gmail authorization expired. Please reconnect Gmail."
        )

    async with httpx.AsyncClient(timeout=30.0) as client:
        refresh_response = await client.post(
            GOOGLE_TOKEN_URL,
            data={
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "refresh_token": token_doc.refresh_token,
                "grant_type": "refresh_token",
            },
        )

    if refresh_response.status_code != 200:
        error_data = {}
        try:
            error_data = refresh_response.json()
        except Exception:
            pass

        error_code = error_data.get("error", "")

        if error_code in ("invalid_grant", "invalid_token"):
            # Refresh token has been revoked
            raise OAuthError(
                "Google refresh token has been revoked. "
                "Please reconnect Google at /dashboard/connectors."
            )

        raise RuntimeError(
            f"Google token refresh failed. "
            f"Status: {refresh_response.status_code}. "
            f"Response: {refresh_response.text}"
        )

    refreshed = refresh_response.json()
    new_access_token = refreshed.get("access_token")
    new_expires_in = refreshed.get("expires_in", 3600)

    if not new_access_token:
        raise RuntimeError(
            "Google token refresh did not return a new access token."
        )

    from datetime import timedelta
    new_expiry = (
        datetime.now(timezone.utc) + timedelta(seconds=new_expires_in)
    ).timestamp()

    # Update the token document
    token_doc.access_token = new_access_token
    token_doc.token_expiry = new_expiry
    await token_doc.save()

    print(
        f"[GoogleTokenService] Token refreshed successfully for "
        f"{token_doc.google_email}"
    )

    return new_access_token
