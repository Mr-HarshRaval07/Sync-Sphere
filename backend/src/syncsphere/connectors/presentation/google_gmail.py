import base64
import logging
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import httpx

logger = logging.getLogger("syncsphere.connectors.presentation.google_gmail")

GOOGLE_GMAIL_SEND_URL = (
    "https://gmail.googleapis.com/gmail/v1/users/me/messages/send"
)


def generate_gmail_thread_reference(
    thread_id: str | None,
    message_id: str | None = None
) -> dict:
    """
    Generate Gmail thread reference metadata.
    
    NOTE / FUTURE COMPATIBILITY:
    - The Gmail API exposes `threadId` and `messageId`.
    - The Gmail REST API does NOT officially publish a web permalink property (`webUrl` / `htmlLink`)
      in its resource schema contract.
    - The generated URL (`https://mail.google.com/mail/u/0/#all/{thread_id}`) relies on current Gmail
      web application hash routing and is treated strictly as a BEST-EFFORT convenience link.
    - `officiallySupported` is set to False to signify that this URL is best-effort.
      If disabled or unroutable, downstream consumers fall back gracefully to Message ID & Thread ID displays.
    """
    if not thread_id:
        return {
            "threadId": None,
            "messageId": message_id,
            "threadUrl": None,
            "officiallySupported": False
        }
    
    thread_url = f"https://mail.google.com/mail/u/0/#all/{thread_id}"
    return {
        "threadId": thread_id,
        "messageId": message_id,
        "threadUrl": thread_url,
        "officiallySupported": False
    }


def format_slack_email_notification(
    recipient: str,
    subject: str,
    sent_timestamp: str,
    message_id: str,
    thread_id: str,
    gmail_thread_url: str | None = None
) -> str:
    """
    Format Slack notification message for a sent Gmail email according to exact specification.
    If a direct Gmail thread URL is available/supported, it is included.
    Otherwise, 'Direct Gmail thread link unavailable.' is displayed with Message ID and Thread ID.
    """
    if gmail_thread_url:
        return (
            "📧 Email Sent Successfully\n\n"
            f"Recipient:\n{recipient}\n\n"
            f"Subject:\n{subject}\n\n"
            f"Sent At:\n{sent_timestamp}\n\n"
            f"Open Email Thread:\n{gmail_thread_url}\n\n"
            f"Thread ID:\n{thread_id}\n\n"
            f"Message ID:\n{message_id}"
        )
    else:
        return (
            "📧 Email Sent Successfully\n\n"
            "Direct Gmail thread link unavailable.\n\n"
            f"Recipient:\n{recipient}\n\n"
            f"Subject:\n{subject}\n\n"
            f"Sent At:\n{sent_timestamp}\n\n"
            f"Thread ID:\n{thread_id}\n\n"
            f"Message ID:\n{message_id}"
        )


async def send_gmail_email(
    to: str,
    subject: str,
    body: str,
    organization_id: str | None = None,
    google_email: str | None = None,
    html_body: str | None = None,
    user_id: str | None = None,
    **kwargs
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
        Gmail API response dict with message id, threadId, labelIds, internalDate,
        sentTimestamp, recipient, subject, threadReference, and Slack notification text.

    Raises:
        RuntimeError: If no Google token, token refresh fails, or Gmail API fails
    """
    from syncsphere.connectors.application.google_token_service import (
        get_valid_google_token,
    )

    access_token = await get_valid_google_token(
        google_email=google_email,
        organization_id=organization_id,
        user_id=user_id,
        required_scopes=["https://www.googleapis.com/auth/gmail.send"]
    )

    import re
    email_regex = r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)"
    if not re.match(email_regex, to.strip()):
        raise ValueError(f"Address not found / Invalid recipient email format: '{to}'")

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
    message_id = result.get("id")
    thread_id = result.get("threadId")
    label_ids = result.get("labelIds", ["SENT"])

    # Attempt to retrieve internalDate timestamp via messages.get if available
    internal_date = result.get("internalDate")
    if not internal_date and message_id:
        try:
            async with httpx.AsyncClient(timeout=10.0) as get_client:
                get_resp = await get_client.get(
                    f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{message_id}?format=minimal",
                    headers=headers
                )
                if get_resp.status_code == 200:
                    msg_details = get_resp.json()
                    internal_date = msg_details.get("internalDate")
                    if msg_details.get("labelIds"):
                        label_ids = msg_details.get("labelIds")
        except Exception as e:
            logger.debug("Failed to fetch extended message details: %s", e)

    if internal_date:
        try:
            from datetime import timezone
            sent_dt = datetime.fromtimestamp(int(internal_date) / 1000.0, tz=timezone.utc)
            sent_timestamp = sent_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        except Exception:
            from datetime import timezone
            sent_timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    else:
        from datetime import timezone
        sent_timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # Generate Gmail thread reference via central helper (best-effort)
    thread_ref = generate_gmail_thread_reference(thread_id=thread_id, message_id=message_id)
    gmail_thread_url = thread_ref.get("threadUrl")

    slack_text = format_slack_email_notification(
        recipient=to,
        subject=subject,
        sent_timestamp=sent_timestamp,
        message_id=str(message_id or ""),
        thread_id=str(thread_id or ""),
        gmail_thread_url=gmail_thread_url
    )

    logger.info(
        "Email sent successfully: Recipient=%s, Subject=%s, Message ID=%s, Thread ID=%s, BestEffortURL=%s",
        to, subject, message_id, thread_id, gmail_thread_url
    )

    output_payload = {
        "id": message_id,
        "messageId": message_id,
        "threadId": thread_id,
        "labelIds": label_ids,
        "internalDate": internal_date,
        "recipient": to,
        "subject": subject,
        "sentTimestamp": sent_timestamp,
        "threadReference": thread_ref,
        "gmailThreadUrl": gmail_thread_url,
        "thread_url": gmail_thread_url,
        "slack_notification_text": slack_text
    }

    return output_payload