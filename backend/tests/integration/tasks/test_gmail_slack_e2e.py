import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from syncsphere.connectors.presentation.google_gmail import (
    send_gmail_email,
    format_slack_email_notification
)
from syncsphere.tasks.documents import TaskDocument, TaskAutomation


@pytest.mark.asyncio
async def test_end_to_end_gmail_slack_pipeline():
    # 1. Simulate Gmail API send response
    mock_send_resp = MagicMock()
    mock_send_resp.status_code = 200
    mock_send_resp.json.return_value = {
        "id": "18f88c3a1b2c3d4e",
        "threadId": "18f88c3a1b2c3d4e",
        "labelIds": ["SENT"],
    }

    mock_get_resp = MagicMock()
    mock_get_resp.status_code = 200
    mock_get_resp.json.return_value = {
        "id": "18f88c3a1b2c3d4e",
        "threadId": "18f88c3a1b2c3d4e",
        "internalDate": "1770000000000",
        "labelIds": ["SENT", "INBOX"],
    }

    with patch("syncsphere.connectors.application.google_token_service.get_valid_google_token", new_callable=AsyncMock) as mock_token:
        mock_token.return_value = "mock_access_token"

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_send_resp
            with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
                mock_get.return_value = mock_get_resp

                # Execute Gmail email send
                result = await send_gmail_email(
                    to="client@acme.ai",
                    subject="Q3 Roadmap Sync",
                    body="Hello team, here is the Q3 roadmap summary."
                )

                # 2. Verify Gmail Return Metadata
                assert result["recipient"] == "client@acme.ai"
                assert result["subject"] == "Q3 Roadmap Sync"
                assert result["messageId"] == "18f88c3a1b2c3d4e"
                assert result["threadId"] == "18f88c3a1b2c3d4e"
                assert result["gmailThreadUrl"] == "https://mail.google.com/mail/u/0/#all/18f88c3a1b2c3d4e"
                assert "sentTimestamp" in result

                # 3. Verify Slack Notification Generation
                slack_msg = format_slack_email_notification(
                    recipient=result["recipient"],
                    subject=result["subject"],
                    sent_timestamp=result["sentTimestamp"],
                    message_id=result["messageId"],
                    thread_id=result["threadId"],
                    gmail_thread_url=result["gmailThreadUrl"]
                )

                assert "📧 Email Sent Successfully" in slack_msg
                assert "client@acme.ai" in slack_msg
                assert "Q3 Roadmap Sync" in slack_msg
                assert "18f88c3a1b2c3d4e" in slack_msg
                assert "Open Email Thread:" in slack_msg
                assert "https://mail.google.com/mail/u/0/#all/18f88c3a1b2c3d4e" in slack_msg
                assert "https://mail.google.com/" not in slack_msg.replace(result["gmailThreadUrl"], "")

                # 4. Verify MongoDB Task Automation Document Schema Structure
                automation_item = TaskAutomation(
                    action="gmail.send_email",
                    config={"to": "client@acme.ai", "subject": "Q3 Roadmap Sync"},
                    status="success",
                    result=result
                )

                stored_result = automation_item.result
                assert stored_result["recipient"] == "client@acme.ai"
                assert stored_result["subject"] == "Q3 Roadmap Sync"
                assert stored_result["messageId"] == "18f88c3a1b2c3d4e"
                assert stored_result["threadId"] == "18f88c3a1b2c3d4e"
                assert stored_result["gmailThreadUrl"] == "https://mail.google.com/mail/u/0/#all/18f88c3a1b2c3d4e"
                assert stored_result["sentTimestamp"] == result["sentTimestamp"]
