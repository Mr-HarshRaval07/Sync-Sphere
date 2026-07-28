"""
Gmail Connector — Real Implementation

Sends email via Gmail API using the stored Google OAuth token.
Token is automatically refreshed if expired.
"""
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import httpx


GOOGLE_GMAIL_SEND_URL = (
    "https://gmail.googleapis.com/gmail/v1/users/me/messages/send"
)


async def send_gmail_email(
    to: str,
    subject: str,
    body: str,
    organization_id: str | None = None,
    google_email: str | None = None,
    html_body: str | None = None,
) -> dict:
    """
    Send an email through the Gmail API.

    Automatically fetches and refreshes the stored Google OAuth token.
    Does NOT accept an access_token parameter — tokens stay backend-only.

    Args:
        to: Recipient email address
        subject: Email subject line
        body: Plain text email body
        organization_id: Optional org scope for multi-tenant
        google_email: Optional Google account email for lookup
        html_body: Optional HTML body (creates multipart/alternative message)

    Returns:
        Gmail API response dict with message id, labelIds, etc.

    Raises:
        RuntimeError: If no Google token, token refresh fails, or Gmail API fails
    """
    from syncsphere.connectors.application.google_token_service import (
        get_valid_google_token,
    )

    # Obtain valid access token (auto-refreshes if expired)
    access_token = await get_valid_google_token(
        google_email=google_email,
        organization_id=organization_id,
    )

    # Build message
    if html_body:
        message = MIMEMultipart("alternative")
        message["To"] = to
        message["Subject"] = subject
        message.attach(MIMEText(body, "plain", "utf-8"))
        message.attach(MIMEText(html_body, "html", "utf-8"))
    else:
        message = MIMEText(body, "plain", "utf-8")
        message["To"] = to
        message["Subject"] = subject

    raw_message = base64.urlsafe_b64encode(
        message.as_bytes()
    ).decode("utf-8")

    payload = {"raw": raw_message}

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            GOOGLE_GMAIL_SEND_URL,
            headers=headers,
            json=payload,
        )

    if response.status_code in (401, 403):
        from syncsphere.connectors.application.exceptions import OAuthError
        raise OAuthError(
            f"Google API Permission Error (Status: {response.status_code}). "
            f"Missing required scopes or token expired. "
            f"Please reconnect Google."
        )
    elif response.status_code not in (200, 201):
        error_info = {}
        try:
            error_info = response.json()
        except Exception:
            pass

        raise RuntimeError(
            f"Gmail API failed to send email. "
            f"Status: {response.status_code}. "
            f"Error: {error_info.get('error', {}).get('message', response.text)}"
        )

    result = response.json()
    print(
        f"[Gmail] Email sent to {to}. "
        f"Message ID: {result.get('id')}"
    )
    return result