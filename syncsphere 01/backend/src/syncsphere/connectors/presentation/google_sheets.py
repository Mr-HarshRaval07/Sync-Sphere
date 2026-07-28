"""
Google Sheets Connector — Real Implementation

Appends rows and reads data from Google Sheets using the stored OAuth token.
Token is automatically refreshed if expired.
"""
import httpx


async def append_google_sheet_row(
    spreadsheet_id: str,
    range_name: str,
    values: list,
    organization_id: str | None = None,
    google_email: str | None = None,
) -> dict:
    """
    Append one row of data to a Google Sheet.

    Automatically fetches and refreshes the stored Google OAuth token.

    Args:
        spreadsheet_id: The Google Sheets spreadsheet ID (from the URL)
        range_name: Sheet range e.g. "Sheet1!A1" or "Sheet1"
        values: List of cell values for this row e.g. ["Title", "Pending", "2026-07-22"]
        organization_id: Optional org scope for multi-tenant
        google_email: Optional Google account email for lookup

    Returns:
        Google Sheets API append response dict

    Raises:
        RuntimeError: If no Google token, refresh fails, or Sheets API fails
    """
    from syncsphere.connectors.application.google_token_service import (
        get_valid_google_token,
    )

    access_token = await get_valid_google_token(
        google_email=google_email,
        organization_id=organization_id,
    )

    url = (
        f"https://sheets.googleapis.com/v4/spreadsheets/"
        f"{spreadsheet_id}/values/{range_name}:append"
    )

    params = {
        "valueInputOption": "USER_ENTERED",
        "insertDataOption": "INSERT_ROWS",
    }

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    payload = {
        "values": [values],
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            url,
            params=params,
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
    elif response.status_code != 200:
        error_info = {}
        try:
            error_info = response.json()
        except Exception:
            pass

        raise RuntimeError(
            f"Google Sheets API failed to append row. "
            f"Status: {response.status_code}. "
            f"Error: {error_info.get('error', {}).get('message', response.text)}"
        )

    result = response.json()
    updates = result.get("updates", {})
    print(
        f"[GoogleSheets] Appended row to {spreadsheet_id}:{range_name}. "
        f"Updated cells: {updates.get('updatedCells', 0)}"
    )
    return result


async def read_google_sheet_rows(
    spreadsheet_id: str,
    range_name: str,
    organization_id: str | None = None,
    google_email: str | None = None,
) -> list:
    """
    Read rows from a Google Sheet range.

    Returns:
        List of rows, where each row is a list of cell values
    """
    from syncsphere.connectors.application.google_token_service import (
        get_valid_google_token,
    )

    access_token = await get_valid_google_token(
        google_email=google_email,
        organization_id=organization_id,
    )

    url = (
        f"https://sheets.googleapis.com/v4/spreadsheets/"
        f"{spreadsheet_id}/values/{range_name}"
    )

    headers = {
        "Authorization": f"Bearer {access_token}",
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url, headers=headers)

    if response.status_code in (401, 403):
        from syncsphere.connectors.application.exceptions import OAuthError
        raise OAuthError(
            f"Google API Permission Error (Status: {response.status_code}). "
            f"Missing required scopes or token expired. "
            f"Please reconnect Google."
        )
    elif response.status_code != 200:
        raise RuntimeError(
            f"Google Sheets API failed to read rows. "
            f"Status: {response.status_code}. "
            f"Response: {response.text}"
        )

    result = response.json()
    return result.get("values", [])