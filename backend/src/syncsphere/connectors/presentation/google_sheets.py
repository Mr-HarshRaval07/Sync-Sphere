"""
Google Sheets Connector — Real Implementation

Appends rows and reads data from Google Sheets using the stored OAuth token.
Token is automatically refreshed if expired. Supports automatic spreadsheet
resolution by name, URL, or default lookup.
"""
import re
import httpx


async def _resolve_spreadsheet_id(
    access_token: str,
    spreadsheet_input: str | None = None,
    user_id: str | None = None,
) -> tuple[str, str]:
    """
    Resolves a spreadsheet name, title, URL, or ID into a valid Google Spreadsheet ID and Title.
    If no name or ID is provided, retrieves the user's most recently modified spreadsheet or creates a new one.

    Returns:
        (spreadsheet_id, title)
    """
    raw_input = (spreadsheet_input or "").strip()

    # 1. If input is empty, try user default preference if available
    if not raw_input and user_id:
        try:
            from syncsphere.identity.infrastructure.documents.user_document import UserDocument
            user = await UserDocument.get(user_id)
            if user and hasattr(user, "preferences") and user.preferences:
                pref_id = getattr(user.preferences, "default_google_sheets_id", None)
                if pref_id and str(pref_id).strip():
                    return str(pref_id).strip(), "Default Spreadsheet"
        except Exception:
            pass

    # 2. Check if input is a Google Sheets URL
    if "docs.google.com/spreadsheets/d/" in raw_input:
        match = re.search(r"/spreadsheets/d/([a-zA-Z0-9_-]+)", raw_input)
        if match:
            return match.group(1), "Spreadsheet from URL"

    # 3. Check if input is already a raw Google Spreadsheet ID (base64url 25-100 chars, no spaces)
    if raw_input and re.match(r"^[a-zA-Z0-9_-]{25,100}$", raw_input):
        return raw_input, raw_input

    # 4. Input is a Spreadsheet Name (or empty input)
    headers = {"Authorization": f"Bearer {access_token}"}

    if raw_input:
        escaped_name = raw_input.replace("'", "\\'")
        # Search Google Drive API for spreadsheet with matching name
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.get(
                    "https://www.googleapis.com/drive/v3/files",
                    headers=headers,
                    params={
                        "q": f"mimeType='application/vnd.google-apps.spreadsheet' and name='{escaped_name}' and trashed=false",
                        "orderBy": "modifiedTime desc",
                        "pageSize": 1,
                    },
                )
                if res.status_code == 200:
                    data = res.json()
                    files = data.get("files", [])
                    if files:
                        return files[0]["id"], files[0].get("name", raw_input)
        except Exception:
            pass

        # Partial search match if exact match returned nothing
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.get(
                    "https://www.googleapis.com/drive/v3/files",
                    headers=headers,
                    params={
                        "q": f"mimeType='application/vnd.google-apps.spreadsheet' and name contains '{escaped_name}' and trashed=false",
                        "orderBy": "modifiedTime desc",
                        "pageSize": 1,
                    },
                )
                if res.status_code == 200:
                    data = res.json()
                    files = data.get("files", [])
                    if files:
                        return files[0]["id"], files[0].get("name", raw_input)
        except Exception:
            pass

        create_title = raw_input
    else:
        # No input provided: find user's most recently modified Google Sheet
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.get(
                    "https://www.googleapis.com/drive/v3/files",
                    headers=headers,
                    params={
                        "q": "mimeType='application/vnd.google-apps.spreadsheet' and trashed=false",
                        "orderBy": "modifiedTime desc",
                        "pageSize": 1,
                    },
                )
                if res.status_code == 200:
                    data = res.json()
                    files = data.get("files", [])
                    if files:
                        return files[0]["id"], files[0].get("name", "Recent Spreadsheet")
        except Exception:
            pass

        create_title = "SyncSphere Automations"

    # Create new Google Spreadsheet via Sheets API v4
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            create_res = await client.post(
                "https://sheets.googleapis.com/v4/spreadsheets",
                headers={**headers, "Content-Type": "application/json"},
                json={"properties": {"title": create_title}},
            )
            if create_res.status_code == 200:
                created_data = create_res.json()
                sheet_id = created_data.get("spreadsheetId")
                sheet_title = created_data.get("properties", {}).get("title", create_title)
                if sheet_id:
                    print(f"[GoogleSheets] Created new spreadsheet '{sheet_title}' with ID: {sheet_id}")
                    return sheet_id, sheet_title
    except Exception as e:
        print(f"[GoogleSheets] Failed to create spreadsheet automatically: {e}")

    raise RuntimeError(
        f"Unable to locate or create a Google Spreadsheet for '{create_title}'. "
        f"Please verify your Google OAuth permissions."
    )


async def append_google_sheet_row(
    spreadsheet_id: str | None = None,
    range_name: str | None = "Sheet1",
    values: list = None,
    organization_id: str | None = None,
    google_email: str | None = None,
    user_id: str | None = None,
    spreadsheet_name: str | None = None,
    spreadsheet: str | None = None,
    **kwargs
) -> dict:
    """
    Append one row of data to a Google Sheet.

    Automatically resolves spreadsheet name, URL, or ID.
    Fetches and refreshes stored Google OAuth tokens.

    Args:
        spreadsheet_id: Optional Spreadsheet ID, URL, or Name
        range_name: Sheet range e.g. "Sheet1"
        values: List of cell values for this row e.g. ["Title", "Pending", "2026-07-22"]
        organization_id: Optional org scope for multi-tenant
        google_email: Optional Google account email for lookup

    Returns:
        Google Sheets API append response dict
    """
    from syncsphere.connectors.application.google_token_service import (
        get_valid_google_token,
    )

    target_input = (
        spreadsheet_id
        or spreadsheet_name
        or spreadsheet
        or kwargs.get("name")
        or kwargs.get("title")
        or kwargs.get("spreadsheet_title")
    )

    if not range_name or not str(range_name).strip():
        range_name = "Sheet1"

    if isinstance(values, str):
        values = [v.strip() for v in values.split(",") if v.strip()]
    elif not isinstance(values, list):
        if values is None:
            values = []
        else:
            values = [str(values)]

    if not values:
        raise ValueError("Google Sheets append_row requires at least one value to append. Ensure 'values' is provided as a list.")

    access_token = await get_valid_google_token(
        google_email=google_email,
        organization_id=organization_id,
        user_id=user_id,
    )

    actual_spreadsheet_id, sheet_title = await _resolve_spreadsheet_id(
        access_token, target_input, user_id=user_id
    )

    url = (
        f"https://sheets.googleapis.com/v4/spreadsheets/"
        f"{actual_spreadsheet_id}/values/{range_name}:append"
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
        f"[GoogleSheets] Appended row to {actual_spreadsheet_id}:{range_name}. "
        f"Updated cells: {updates.get('updatedCells', 0)}"
    )
    result["spreadsheet_id"] = actual_spreadsheet_id
    result["spreadsheet_title"] = sheet_title
    result["spreadsheet_url"] = f"https://docs.google.com/spreadsheets/d/{actual_spreadsheet_id}/edit"
    return result


async def read_google_sheet_rows(
    spreadsheet_id: str | None = None,
    range_name: str | None = "Sheet1",
    organization_id: str | None = None,
    google_email: str | None = None,
    user_id: str | None = None,
    spreadsheet_name: str | None = None,
    spreadsheet: str | None = None,
    **kwargs
) -> list:
    """
    Read rows from a Google Sheet range.

    Returns:
        List of rows, where each row is a list of cell values
    """
    from syncsphere.connectors.application.google_token_service import (
        get_valid_google_token,
    )

    target_input = (
        spreadsheet_id
        or spreadsheet_name
        or spreadsheet
        or kwargs.get("name")
        or kwargs.get("title")
        or kwargs.get("spreadsheet_title")
    )

    if not range_name or not str(range_name).strip():
        range_name = "Sheet1"

    access_token = await get_valid_google_token(
        google_email=google_email,
        organization_id=organization_id,
        user_id=user_id
    )

    actual_spreadsheet_id, _ = await _resolve_spreadsheet_id(
        access_token, target_input, user_id=user_id
    )

    url = (
        f"https://sheets.googleapis.com/v4/spreadsheets/"
        f"{actual_spreadsheet_id}/values/{range_name}"
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