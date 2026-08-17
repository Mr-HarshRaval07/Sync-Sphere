import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from syncsphere.connectors.presentation.google_gmail import (
    send_gmail_email,
    format_slack_email_notification,
    generate_gmail_thread_reference
)


def test_generate_gmail_thread_reference():
    ref = generate_gmail_thread_reference("thread_123", "msg_456")
    assert ref["threadId"] == "thread_123"
    assert ref["messageId"] == "msg_456"
    assert ref["threadUrl"] == "https://mail.google.com/mail/u/0/#all/thread_123"
    assert ref["officiallySupported"] is False

    ref_empty = generate_gmail_thread_reference(None)
    assert ref_empty["threadUrl"] is None
    assert ref_empty["officiallySupported"] is False


def test_format_slack_email_notification_with_url():
    text = format_slack_email_notification(
        recipient="user@example.com",
        subject="Project Update",
        sent_timestamp="2026-08-07T12:00:00Z",
        message_id="msg_12345",
        thread_id="thread_67890",
        gmail_thread_url="https://mail.google.com/mail/u/0/#all/thread_67890"
    )
    assert "📧 Email Sent Successfully" in text
    assert "user@example.com" in text
    assert "Project Update" in text
    assert "2026-08-07T12:00:00Z" in text
    assert "msg_12345" in text
    assert "thread_67890" in text
    assert "Open Email Thread:" in text
    assert "https://mail.google.com/mail/u/0/#all/thread_67890" in text


def test_format_slack_email_notification_without_url():
    text = format_slack_email_notification(
        recipient="user@example.com",
        subject="Project Update",
        sent_timestamp="2026-08-07T12:00:00Z",
        message_id="msg_12345",
        thread_id="thread_67890",
        gmail_thread_url=None
    )
    assert "📧 Email Sent Successfully" in text
    assert "Direct Gmail thread link unavailable." in text
    assert "user@example.com" in text
    assert "msg_12345" in text
    assert "thread_67890" in text
    assert "Open Email Thread:" not in text


@pytest.mark.asyncio
async def test_send_gmail_email_metadata_capture():
    mock_send_resp = MagicMock()
    mock_send_resp.status_code = 200
    mock_send_resp.json.return_value = {
        "id": "msg_abc123",
        "threadId": "thread_xyz789",
        "labelIds": ["SENT"],
    }

    mock_get_resp = MagicMock()
    mock_get_resp.status_code = 200
    mock_get_resp.json.return_value = {
        "id": "msg_abc123",
        "threadId": "thread_xyz789",
        "internalDate": "1770000000000",
        "labelIds": ["SENT", "INBOX"],
    }

    with patch("syncsphere.connectors.application.google_token_service.get_valid_google_token", new_callable=AsyncMock) as mock_token:
        mock_token.return_value = "mock_access_token"

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_send_resp
            with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
                mock_get.return_value = mock_get_resp

                res = await send_gmail_email(
                    to="alice@acme.ai",
                    subject="Quarterly Report",
                    body="Please find attached report."
                )

                assert res["id"] == "msg_abc123"
                assert res["messageId"] == "msg_abc123"
                assert res["threadId"] == "thread_xyz789"
                assert res["recipient"] == "alice@acme.ai"
                assert res["subject"] == "Quarterly Report"
                assert "sentTimestamp" in res
                assert res["gmailThreadUrl"] == "https://mail.google.com/mail/u/0/#all/thread_xyz789"
                assert "slack_notification_text" in res
                assert "alice@acme.ai" in res["slack_notification_text"]
