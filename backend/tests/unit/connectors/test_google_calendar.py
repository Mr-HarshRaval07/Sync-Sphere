import json
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from syncsphere.connectors.presentation.google_calendar import (
    create_google_calendar_event,
    _parse_to_datetime,
    _clean_attendees,
    _clean_reminders,
    _clean_recurrence,
    _validate_event_payload,
    _get_tz,
)


def test_datetime_parsing_rfc3339():
    tz = _get_tz("Asia/Kolkata")
    
    # Naive string -> aware with timezone offset
    dt = _parse_to_datetime("2026-08-07T10:00:00", tz)
    assert dt is not None
    assert dt.isoformat() == "2026-08-07T10:00:00+05:30"
    
    # Trailing Z -> aware with UTC offset
    dt_z = _parse_to_datetime("2026-08-07T10:00:00Z", tz)
    assert dt_z is not None
    assert dt_z.isoformat() == "2026-08-07T10:00:00+00:00"


def test_attendees_cleaning():
    # String comma separated
    att = _clean_attendees("user1@example.com, user2@example.com")
    assert att == [{"email": "user1@example.com"}, {"email": "user2@example.com"}]
    
    # Mixed valid/invalid
    att2 = _clean_attendees([{"email": "valid@example.com"}, "notanemail", {"email": "invalid"}])
    assert att2 == [{"email": "valid@example.com"}]


def test_reminders_cleaning():
    rem = _clean_reminders({"useDefault": True})
    assert rem == {"useDefault": True}
    
    rem_overrides = _clean_reminders({
        "useDefault": False,
        "overrides": [{"method": "popup", "minutes": 15}, {"method": "invalid", "minutes": -5}]
    })
    assert rem_overrides == {"useDefault": False, "overrides": [{"method": "popup", "minutes": 15}]}


def test_recurrence_cleaning():
    rec = _clean_recurrence("FREQ=DAILY;COUNT=5")
    assert rec == ["RRULE:FREQ=DAILY;COUNT=5"]
    
    rec_list = _clean_recurrence(["RRULE:FREQ=WEEKLY", ""])
    assert rec_list == ["RRULE:FREQ=WEEKLY"]


def test_preflight_validation():
    # Valid payload
    valid_payload = {
        "summary": "Meeting",
        "start": {"dateTime": "2026-08-07T10:00:00+05:30", "timeZone": "Asia/Kolkata"},
        "end": {"dateTime": "2026-08-07T11:00:00+05:30", "timeZone": "Asia/Kolkata"}
    }
    _validate_event_payload(valid_payload)
    
    # Missing summary
    with pytest.raises(ValueError, match="summary"):
        _validate_event_payload({
            "summary": "",
            "start": {"dateTime": "2026-08-07T10:00:00+05:30", "timeZone": "Asia/Kolkata"},
            "end": {"dateTime": "2026-08-07T11:00:00+05:30", "timeZone": "Asia/Kolkata"}
        })


@pytest.mark.asyncio
async def test_create_google_calendar_event_success():
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "id": "event_123",
        "summary": "Team Sync",
        "htmlLink": "https://calendar.google.com/event?id=event_123"
    }

    with patch("syncsphere.connectors.application.google_token_service.get_valid_google_token", return_value="mock_access_token"), \
         patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_response) as mock_post:

        res = await create_google_calendar_event(
            summary="Team Sync",
            start_datetime="2026-08-07T10:00:00",
            end_datetime="2026-08-07T11:00:00",
            timezone="Asia/Kolkata",
            google_email="user@example.com"
        )

        assert res["id"] == "event_123"
        assert res["event_link"] == "https://calendar.google.com/event?id=event_123"
        
        # Verify RFC3339 payload sent to httpx
        called_json = mock_post.call_args.kwargs["json"]
        assert called_json["summary"] == "Team Sync"
        assert called_json["start"]["dateTime"] == "2026-08-07T10:00:00+05:30"
        assert called_json["end"]["dateTime"] == "2026-08-07T11:00:00+05:30"


@pytest.mark.asyncio
async def test_create_google_calendar_event_400_surfaces_exact_field():
    mock_response = MagicMock()
    mock_response.status_code = 400
    mock_response.text = '{"error": {"code": 400, "message": "Invalid Value", "errors": [{"location": "resource.start.dateTime", "message": "Invalid dateTime format", "reason": "invalid"}]}}'
    mock_response.json.return_value = {
        "error": {
            "code": 400,
            "message": "Invalid Value",
            "errors": [
                {
                    "location": "resource.start.dateTime",
                    "message": "Invalid dateTime format",
                    "reason": "invalid"
                }
            ]
        }
    }

    with patch("syncsphere.connectors.application.google_token_service.get_valid_google_token", return_value="mock_access_token"), \
         patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_response):

        with pytest.raises(RuntimeError) as exc_info:
            await create_google_calendar_event(
                summary="Test Event",
                start_datetime="2026-08-07T10:00:00",
                end_datetime="2026-08-07T11:00:00"
            )

        err_msg = str(exc_info.value)
        assert "Status: 400" in err_msg
        assert "resource.start.dateTime" in err_msg
        assert "Invalid dateTime format" in err_msg
