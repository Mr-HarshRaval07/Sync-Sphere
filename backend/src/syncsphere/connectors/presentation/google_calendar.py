"""
Google Calendar Connector — Real Implementation

Creates calendar events via the Google Calendar API using the stored OAuth token.
Token is automatically refreshed if expired.
"""
import json
import logging
import re
from datetime import datetime, timedelta, timezone
from typing import Any, Optional
import zoneinfo

import httpx

logger = logging.getLogger(__name__)

GOOGLE_CALENDAR_CREATE_EVENT_URL = (
    "https://www.googleapis.com/calendar/v3/calendars/primary/events"
)


def _get_tz(tz_name: str | None) -> timezone | zoneinfo.ZoneInfo:
    """Return valid ZoneInfo or fallback timezone."""
    if not tz_name or not isinstance(tz_name, str):
        tz_name = "Asia/Kolkata"
    try:
        return zoneinfo.ZoneInfo(tz_name.strip())
    except Exception:
        return timezone.utc


def _parse_to_datetime(val: Any, tz_obj: timezone | zoneinfo.ZoneInfo) -> Optional[datetime]:
    """Parse datetime input (string/dict) into a timezone-aware datetime."""
    if not val:
        return None
    if isinstance(val, dict):
        val = val.get("dateTime") or val.get("date") or val.get("value")
    if not isinstance(val, str) or not val.strip():
        return None

    s = val.strip()
    # Replace trailing Z with explicit UTC offset
    if s.endswith("Z") or s.endswith("z"):
        s = s[:-1] + "+00:00"

    try:
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=tz_obj)
        return dt
    except Exception:
        return None


def _clean_attendees(attendees: Any) -> Optional[list[dict]]:
    """Validate and normalize attendees list into standard Google Calendar format."""
    if not attendees:
        return None
    res = []
    items = []
    if isinstance(attendees, str):
        items = [x.strip() for x in attendees.split(",") if x.strip()]
    elif isinstance(attendees, list):
        items = attendees

    for item in items:
        if isinstance(item, str):
            email = item.strip()
            if "@" in email and "." in email:
                res.append({"email": email})
        elif isinstance(item, dict):
            email = str(item.get("email", "")).strip()
            if "@" in email and "." in email:
                att = {"email": email}
                if item.get("displayName"):
                    att["displayName"] = str(item["displayName"]).strip()
                res.append(att)

    return res if res else None


def _clean_reminders(reminders: Any) -> Optional[dict]:
    """Validate reminders dict structure."""
    if not isinstance(reminders, dict):
        return None
    use_default = bool(reminders.get("useDefault", True))
    overrides_raw = reminders.get("overrides")
    clean_overrides = []
    if isinstance(overrides_raw, list):
        for o in overrides_raw:
            if isinstance(o, dict):
                method = str(o.get("method", "")).lower()
                minutes = o.get("minutes")
                if method in ("email", "popup") and isinstance(minutes, int) and minutes >= 0:
                    clean_overrides.append({"method": method, "minutes": minutes})

    if clean_overrides:
        return {"useDefault": False, "overrides": clean_overrides}
    return {"useDefault": use_default}


def _clean_recurrence(recurrence: Any) -> Optional[list[str]]:
    """Validate recurrence lines."""
    if not recurrence:
        return None
    lines = []
    if isinstance(recurrence, str):
        lines = [recurrence]
    elif isinstance(recurrence, list):
        lines = recurrence

    clean_lines = []
    for line in lines:
        if isinstance(line, str):
            s = line.strip()
            if not s:
                continue
            if not any(s.startswith(prefix) for prefix in ("RRULE:", "EXRULE:", "RDATE:", "EXDATE:")):
                s = f"RRULE:{s}"
            clean_lines.append(s)

    return clean_lines if clean_lines else None


def _validate_event_payload(payload: dict) -> None:
    """Server-side preflight validation before calling Google Calendar API."""
    if not payload.get("summary"):
        raise ValueError("Google Calendar event payload missing required field 'summary'")

    start = payload.get("start")
    if not isinstance(start, dict) or not start.get("dateTime") or not start.get("timeZone"):
        raise ValueError("Google Calendar event payload missing valid 'start' dateTime and timeZone")

    end = payload.get("end")
    if not isinstance(end, dict) or not end.get("dateTime") or not end.get("timeZone"):
        raise ValueError("Google Calendar event payload missing valid 'end' dateTime and timeZone")

    # RFC3339 format validation
    rfc3339_regex = r"^\d{4}-\d{2}-\d{2}[TT ]\d{2}:\d{2}:\d{2}(\.\d+)?([ZZz]|([+-]\d{2}:?\d{2}))?$"
    if not re.match(rfc3339_regex, start["dateTime"]):
        raise ValueError(f"Start datetime '{start['dateTime']}' is not in valid RFC3339 format")
    if not re.match(rfc3339_regex, end["dateTime"]):
        raise ValueError(f"End datetime '{end['dateTime']}' is not in valid RFC3339 format")


async def create_google_calendar_event(
    summary: str | None = None,
    start_datetime: str | None = None,
    end_datetime: str | None = None,
    description: Optional[str] = None,
    timezone: str = "Asia/Kolkata",
    organization_id: str | None = None,
    google_email: str | None = None,
    user_id: str | None = None,
    attendees: list | str | None = None,
    reminders: dict | None = None,
    recurrence: list | str | None = None,
    location: str | None = None,
    **kwargs
) -> dict:
    """
    Create an event in the user's primary Google Calendar.

    Automatically fetches and refreshes the stored Google OAuth token.

    Args:
        summary: Event title
        start_datetime: Start time in ISO 8601 / RFC3339 format
        end_datetime: End time in ISO 8601 / RFC3339 format
        description: Optional event description
        timezone: IANA timezone string (default: Asia/Kolkata)
        organization_id: Optional org scope for multi-tenant
        google_email: Optional Google account email for lookup
        user_id: Optional user ID for lookup
        attendees: Optional list of attendees
        reminders: Optional reminders config
        recurrence: Optional RRULE list
        location: Optional location string

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
        user_id=user_id,
    )

    # Extract & normalize summary
    summary_str = summary or kwargs.get("title") or kwargs.get("name") or kwargs.get("event_name")
    if not summary_str or not str(summary_str).strip():
        summary_str = "New Event"
    else:
        summary_str = str(summary_str).strip()

    # Extract & normalize timezone
    tz_name = timezone or kwargs.get("timeZone") or kwargs.get("tz") or "Asia/Kolkata"
    tz_obj = _get_tz(tz_name)
    tz_string = tz_name if isinstance(tz_name, str) and tz_name.strip() else "Asia/Kolkata"

    # Extract & normalize start / end datetimes
    raw_start = start_datetime or kwargs.get("start_time") or kwargs.get("start") or kwargs.get("start_date") or kwargs.get("startTime")
    raw_end = end_datetime or kwargs.get("end_time") or kwargs.get("end") or kwargs.get("end_date") or kwargs.get("endTime")

    start_dt = _parse_to_datetime(raw_start, tz_obj)
    if not start_dt:
        start_dt = datetime.now(tz_obj) + timedelta(minutes=10)

    end_dt = _parse_to_datetime(raw_end, tz_obj)
    if not end_dt or end_dt <= start_dt:
        end_dt = start_dt + timedelta(hours=1)

    # Format datetimes in strict RFC3339 ISO format with timezone offset
    start_rfc3339 = start_dt.isoformat()
    end_rfc3339 = end_dt.isoformat()

    # Build event payload
    event: dict[str, Any] = {
        "summary": summary_str,
        "start": {
            "dateTime": start_rfc3339,
            "timeZone": tz_string,
        },
        "end": {
            "dateTime": end_rfc3339,
            "timeZone": tz_string,
        },
    }

    # Optional description
    desc_val = description or kwargs.get("description")
    if desc_val and str(desc_val).strip():
        event["description"] = str(desc_val).strip()

    # Optional location
    loc_val = location or kwargs.get("location")
    if loc_val and str(loc_val).strip():
        event["location"] = str(loc_val).strip()

    # Optional attendees
    att_val = attendees if attendees is not None else kwargs.get("attendees")
    clean_att = _clean_attendees(att_val)
    if clean_att:
        event["attendees"] = clean_att

    # Optional reminders
    rem_val = reminders if reminders is not None else kwargs.get("reminders")
    clean_rem = _clean_reminders(rem_val)
    if clean_rem:
        event["reminders"] = clean_rem

    # Optional recurrence
    rec_val = recurrence if recurrence is not None else kwargs.get("recurrence")
    clean_rec = _clean_recurrence(rec_val)
    if clean_rec:
        event["recurrence"] = clean_rec

    # Perform server-side preflight validation
    _validate_event_payload(event)

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    logger.info(f"[GoogleCalendar] Sending payload to Google API: {json.dumps(event)}")

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

        logger.error(
            f"[GoogleCalendar] Event creation failed with status {response.status_code}.\n"
            f"Request payload sent: {json.dumps(event)}\n"
            f"Google API response body: {response.text}"
        )

        detailed_msg = ""
        if isinstance(error_info, dict) and "error" in error_info:
            err_dict = error_info["error"]
            base_msg = err_dict.get("message", response.text)
            sub_errors = err_dict.get("errors", [])
            err_details = []
            if isinstance(sub_errors, list):
                for sub in sub_errors:
                    if isinstance(sub, dict):
                        loc = sub.get("location") or sub.get("domain") or "field"
                        reason = sub.get("reason", "")
                        msg = sub.get("message", "")
                        err_details.append(f"Field/Location '{loc}': {msg} (reason: {reason})")

            if err_details:
                detailed_msg = f"{base_msg} -> " + "; ".join(err_details)
            else:
                detailed_msg = base_msg

        if not detailed_msg:
            detailed_msg = response.text or "Bad Request"

        raise RuntimeError(
            f"Google Calendar API failed to create event. "
            f"Status: {response.status_code}. "
            f"Error: {detailed_msg}"
        )

    result = response.json()
    logger.info(
        f"[GoogleCalendar] Event created: {result.get('summary')}. "
        f"Event ID: {result.get('id')}"
    )
    result["event_link"] = result.get("htmlLink")
    return result