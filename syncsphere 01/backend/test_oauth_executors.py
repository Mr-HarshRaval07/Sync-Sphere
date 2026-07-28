import asyncio
import os
import sys
from datetime import datetime, timedelta

# Add backend to path so we can import modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))

from syncsphere.core.config.settings import settings
from syncsphere.shared_kernel.infrastructure.mongodb.connection import mongodb_manager
from syncsphere.tasks.documents import SlackTokenDocument, GoogleTokenDocument

from syncsphere.connectors.presentation.slack_actions import send_slack_message
from syncsphere.connectors.presentation.google_gmail import send_gmail_email
from syncsphere.connectors.presentation.google_calendar import create_google_calendar_event
from syncsphere.connectors.presentation.google_sheets import append_google_sheet_row

async def test_slack():
    print("================== TEST SLACK ==================")
    token = await SlackTokenDocument.find_one({})
    if not token:
        print("[SLACK] No Slack token found in DB. Test skipped.")
        return False
    
    org_id = token.organization_id
    print(f"[SLACK] Found token for team {token.team_name} in org {org_id}")
    
    try:
        res = await send_slack_message(
            message="Hi from SyncSphere Diagnostics! The execution layer audit is testing Slack isolation.",
            channel="#general", # It will fallback if not found
            organization_id=org_id
        )
        print(f"[SLACK] Success! Message sent: {res.get('ok')}, ts: {res.get('ts')}")
        return True
    except Exception as e:
        print(f"[SLACK] Failed: {e}")
        return False


async def test_google():
    print("================== TEST GOOGLE ==================")
    token = await GoogleTokenDocument.find_one({})
    if not token:
        print("[GOOGLE] No Google token found in DB. Test skipped.")
        return False
        
    org_id = token.organization_id
    email = token.google_email
    print(f"[GOOGLE] Found token for email {email} in org {org_id}")
    
    # 1. GMAIL
    print("--- Testing Gmail ---")
    gmail_success = False
    try:
        res = await send_gmail_email(
            to=email,
            subject="SyncSphere Execution Audit - Gmail Test",
            body="This is an automated test verifying Gmail OAuth executor.",
            organization_id=org_id
        )
        print(f"[GMAIL] Success! Message ID: {res.get('id')}")
        gmail_success = True
    except Exception as e:
        print(f"[GMAIL] Failed: {e}")

    # 2. CALENDAR
    print("--- Testing Calendar ---")
    calendar_success = False
    try:
        now = datetime.now()
        start_time = (now + timedelta(minutes=10)).isoformat()
        end_time = (now + timedelta(minutes=70)).isoformat()
        
        res = await create_google_calendar_event(
            summary="SyncSphere Audit Calendar Test",
            start_datetime=start_time,
            end_datetime=end_time,
            description="Testing isolated execution of Google Calendar.",
            organization_id=org_id
        )
        print(f"[CALENDAR] Success! Event ID: {res.get('id')}")
        calendar_success = True
    except Exception as e:
        print(f"[CALENDAR] Failed: {e}")

    # 3. SHEETS
    print("--- Testing Sheets ---")
    sheets_success = False
    try:
        # Without a valid spreadsheet_id we expect a 404 or a similar error,
        # but at least this exercises the OAuth token fetch and Google Sheets API format.
        res = await append_google_sheet_row(
            spreadsheet_id="INVALID_ID_FOR_AUDIT_TEST",
            range_name="Sheet1",
            values=["SyncSphere", "Audit", "Test"],
            organization_id=org_id
        )
        print(f"[SHEETS] Success! {res}")
        sheets_success = True
    except Exception as e:
        if "404" in str(e):
            print(f"[SHEETS] Appears to have connected successfully, but spreadsheet_id was fake (404 expected). Assuming success on OAuth layer. Error: {e}")
            sheets_success = True
        else:
            print(f"[SHEETS] Failed: {e}")

    return gmail_success and calendar_success and sheets_success

async def run_tests():
    print("Initializing DB...")
    await mongodb_manager.connect([SlackTokenDocument, GoogleTokenDocument])
    print("DB connected.")
    
    await test_slack()
    await test_google()

if __name__ == "__main__":
    asyncio.run(run_tests())
