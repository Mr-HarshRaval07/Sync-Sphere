"""
Google Calendar Connector — Real Implementation

Creates calendar events via the Google Calendar API using the stored OAuth token.
Token is automatically refreshed if expired.
"""
from typing import Optional

import httpx


GOOGLE_CALENDAR_CREATE_EVENT_URL = (
    "https://www.googleapis.com/calendar/v3/calendars/primary/events"
)


async def create_google_calendar_event(
    summary: str,
    start_datetime: str,
    end_datetime: str,
    description: Optional[str] = None,
    timezone: str = "Asia/Kolkata",
    organization_id: str | None = None,
    google_email: str | None = None,
) -> dict:
    """
    Create an event in the user's primary Google Calendar.

    Automatically fetches and refreshes the stored Google OAuth token.

    Args:
        summary: Event title
        start_datetime: Start time in ISO 8601 format (e.g. "2026-07-22T10:00:00")
        end_datetime: End time in ISO 8601 format (e.g. "2026-07-22T11:00:00")
        description: Optional event description
        timezone: IANA timezone string (default: Asia/Kolkata)
        organization_id: Optional org scope for multi-tenant
        google_email: Optional Google account email for lookup

    Returns:
        Google Calendar API event resource dict

    Raises:
        RuntimeError: If no Google token, refresh fails, or Calendar API fails
    """
    from syncsphere.connectors.application.google_token_service import (
        get_valid_google_token,
    )

    access_token = await get_valid_google_token(
        google_email=google_email,
        organization_id=organization_id,
    )

    event = {
        "summary": summary,
        "description": description or "",
        "start": {
            "dateTime": start_datetime,
            "timeZone": timezone,
        },
        "end": {
            "dateTime": end_datetime,
            "timeZone": timezone,
        },
    }

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            GOOGLE_CALENDAR_CREATE_EVENT_URL,
            headers=headers,
            json=event,
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
            f"Google Calendar API failed to create event. "
            f"Status: {response.status_code}. "
            f"Error: {error_info.get('error', {}).get('message', response.text)}"
        )

    result = response.json()
    print(
        f"[GoogleCalendar] Event created: {result.get('summary')}. "
        f"Event ID: {result.get('id')}"
    )
    return result