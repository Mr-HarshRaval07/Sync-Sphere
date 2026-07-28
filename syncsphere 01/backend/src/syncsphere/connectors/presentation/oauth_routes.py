"""
OAuth routes for Google, GitHub, and Slack integrations.

All three providers use the same pattern:
  1. /v1/connect/{provider}   → generate state, set cookie, redirect to provider
  2. /v1/connect/{provider}/callback → validate state cookie, exchange code, save token
"""
import hmac
import secrets
from datetime import datetime, timezone, timedelta
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import RedirectResponse, JSONResponse

from syncsphere.core.config.settings import settings
from syncsphere.shared_kernel.infrastructure.http.dependencies import verify_jwt
from syncsphere.tasks.documents import (
    SlackTokenDocument,
    GoogleTokenDocument,
    GitHubTokenDocument,
    OAuthStateDocument,
)


# -------------------------------------------------------------------
# Router
# -------------------------------------------------------------------

router = APIRouter(
    prefix="/connect",
    tags=["OAuth"],
)


# -------------------------------------------------------------------
# Common OAuth Configuration
# -------------------------------------------------------------------

CONNECTORS_URL = f"{settings.frontend_url}/dashboard/connectors"

COOKIE_SECURE = settings.frontend_url.startswith("https://")

OAUTH_STATE_MAX_AGE_SECONDS = 600


# -------------------------------------------------------------------
# Google OAuth Configuration
# -------------------------------------------------------------------

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"

GOOGLE_SCOPES = [
    "openid",
    "email",
    "profile",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
]


# -------------------------------------------------------------------
# Common OAuth Helpers
# -------------------------------------------------------------------

def connector_redirect(provider: str, result: str) -> RedirectResponse:
    """Redirect user back to the frontend connectors page."""
    query = urlencode({provider: result})
    return RedirectResponse(
        url=f"{CONNECTORS_URL}?{query}",
        status_code=303,
    )

def extract_context_from_cookie(request: Request) -> tuple[str | None, str | None]:
    access_token = request.cookies.get("access_token")
    if not access_token:
        return None, None
    try:
        import jwt
        payload = jwt.decode(
            access_token,
            settings.jwt_secret.get_secret_value(),
            algorithms=[settings.jwt_algorithm]
        )
        return payload.get("org"), payload.get("sub")
    except Exception:
        return None, None



def set_oauth_state_cookie(
    response: RedirectResponse,
    provider: str,
    state: str,
    org_id: str | None = None,
    user_id: str | None = None,
) -> None:
    """Legacy cookie-based state. No longer in use as we use server-side OAuthStateDocument."""
    pass

def delete_oauth_state_cookie(
    response: RedirectResponse,
    provider: str,
) -> None:
    """Legacy cookie deletion."""
    pass

async def create_oauth_state_document(
    provider: str,
    state: str,
    org_id: str | None,
    user_id: str | None,
) -> None:
    """Store raw OAuth state securely in MongoDB."""
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=OAUTH_STATE_MAX_AGE_SECONDS)
    await OAuthStateDocument(
        state=state,
        provider=provider,
        user_id=user_id,
        organization_id=org_id,
        expires_at=expires_at
    ).insert()

async def validate_oauth_state(
    request: Request,
    provider: str,
    received_state: str | None,
) -> OAuthStateDocument:
    """
    Validate state using the server-side OAuthStateDocument.
    If valid, returns the document containing user_id and organization_id.
    """
    if not received_state:
        raise HTTPException(status_code=400, detail="Missing OAuth state parameter.")

    print(f"[{provider}] Validating state: {received_state}")
    doc = await OAuthStateDocument.find_one({"state": received_state, "provider": provider})
    print(f"[{provider}] Validate state result doc: {doc}")
    if not doc:
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired OAuth state. Please try connecting again.",
        )
        
    if datetime.now(timezone.utc) > doc.expires_at.replace(tzinfo=timezone.utc):
        raise HTTPException(
            status_code=400,
            detail="OAuth state expired. Please try connecting again.",
        )
        
    await doc.delete()
    return doc


# ===================================================================
# POST /v1/connect/{provider}/init
# ===================================================================

@router.post("/{provider}/init")
async def init_oauth_connection(
    provider: str,
    claims: dict = Depends(verify_jwt),
):
    """
    Initialize an OAuth flow securely.
    The frontend calls this with a Bearer token (JWT).
    We generate a state, store it server-side, and return the auth URL.
    """
    org_id = claims.get("org")
    user_id = claims.get("sub")
    state = secrets.token_urlsafe(32)
    
    if provider == "google":
        params = {
            "client_id": settings.google_client_id,
            "redirect_uri": settings.google_redirect_uri,
            "response_type": "code",
            "scope": " ".join(GOOGLE_SCOPES),
            "access_type": "offline",
            "prompt": "consent",
            "state": state,
        }
        auth_url = f"{GOOGLE_AUTH_URL}?{urlencode(params)}"
    elif provider == "github":
        params = {
            "client_id": settings.github_client_id,
            "redirect_uri": settings.github_redirect_uri,
            "scope": "repo user",
            "state": state,
            "allow_signup": "false",
        }
        auth_url = f"https://github.com/login/oauth/authorize?{urlencode(params)}"
    elif provider == "slack":
        params = {
            "client_id": settings.slack_client_id,
            "redirect_uri": settings.slack_redirect_uri,
            "scope": "chat:write,chat:write.public,channels:read,channels:manage,channels:history,groups:read,groups:history,reactions:write,users:read,team:read",
            "state": state,
        }
        auth_url = f"https://slack.com/oauth/v2/authorize?{urlencode(params)}"
    else:
        raise HTTPException(status_code=400, detail="Unknown provider")
        
    await create_oauth_state_document(provider, state, org_id, user_id)
    return {"auth_url": auth_url}


# ===================================================================
# GET /v1/connect/status
# ===================================================================

@router.get("/status")
async def connector_status(claims: dict = Depends(verify_jwt)):
    """
    Return real-time connection status for Google, GitHub, and Slack.
    Frontend should use this — NOT rely on query params.
    """
    org_id = claims["org"]
    
    # Google
    google_token = await GoogleTokenDocument.find_one({"organization_id": org_id})
    google_status: dict = {"connected": False}
    if google_token:
        google_status = {
            "connected": True,
            "email": google_token.google_email,
        }

    # GitHub
    github_token = await GitHubTokenDocument.find_one({"organization_id": org_id})
    github_status: dict = {"connected": False}
    if github_token:
        github_status = {
            "connected": True,
            "username": github_token.github_username,
        }

    # Slack
    slack_token = await SlackTokenDocument.find_one({"organization_id": org_id})
    print("========== CONNECTOR STATUS DIAGNOSTIC ==========")
    print(f"Looking for Slack status for org_id: {org_id!r}")
    print(f"Found slack_token: {bool(slack_token)}")
    if slack_token:
        print(f"Slack Token Org ID: {slack_token.organization_id!r}")
    print("================================================")
    
    slack_status: dict = {"connected": False}
    if slack_token:
        slack_status = {
            "connected": True,
            "workspace": slack_token.team_name,
        }

    return JSONResponse({
        "google": google_status,
        "github": github_status,
        "slack": slack_status,
    })


# ===================================================================
# GitHub OAuth
# ===================================================================

@router.get("/github")
async def github_login(request: Request):
    """Start GitHub OAuth flow."""
    org_id, user_id = extract_context_from_cookie(request)
    state = secrets.token_urlsafe(32)

    response = RedirectResponse(
        url=(
            "https://github.com/login/oauth/authorize?"
            + urlencode(
                {
                    "client_id": settings.github_client_id,
                    "redirect_uri": settings.github_redirect_uri,
                    "scope": "repo user",
                    "state": state,
                    "allow_signup": "false",
                }
            )
        )
    )

    set_oauth_state_cookie(response, "github", state, org_id, user_id)
    return response


@router.get("/github/callback")
async def github_callback(
    request: Request,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
):
    """GitHub OAuth callback — validates state, exchanges code, saves token."""

    if error:
        response = connector_redirect("github", "denied")
        return response

    auth_state = await validate_oauth_state(request, "github", state)

    if not code:
        raise HTTPException(
            status_code=400,
            detail="GitHub did not return an authorization code.",
        )

    async with httpx.AsyncClient(timeout=15.0) as client:

        token_response = await client.post(
            "https://github.com/login/oauth/access_token",
            headers={"Accept": "application/json"},
            data={
                "client_id": settings.github_client_id,
                "client_secret": settings.github_client_secret,
                "code": code,
                "redirect_uri": settings.github_redirect_uri,
            },
        )

        token_data = token_response.json()
        access_token = token_data.get("access_token")

        if not access_token:
            raise HTTPException(
                status_code=502,
                detail="GitHub did not return an access token.",
            )

        user_response = await client.get(
            "https://api.github.com/user",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/vnd.github+json",
            },
        )

        user_response.raise_for_status()
        github_user = user_response.json()

    github_username = github_user.get("login", "")
    github_user_id = github_user.get("id", 0)
    scopes = token_data.get("scope", "").split(",") if token_data.get("scope") else []

    org_id = auth_state.organization_id
    user_id = auth_state.user_id

    # Upsert GitHub token
    existing = await GitHubTokenDocument.find_one(
        {"github_username": github_username}
    )

    if existing:
        existing.access_token = access_token
        existing.scopes = scopes
        if org_id:
            existing.organization_id = org_id
        if user_id:
            existing.user_id = user_id
        await existing.save()
        print("GitHub token updated in MongoDB")
    else:
        await GitHubTokenDocument(
            github_username=github_username,
            github_user_id=github_user_id,
            access_token=access_token,
            scopes=scopes,
            organization_id=org_id,
            user_id=user_id,
        ).insert()
        print("GitHub token inserted into MongoDB")

    response = connector_redirect("github", "connected")
    return response


# ===================================================================
# Slack OAuth
# ===================================================================

@router.get("/slack")
async def slack_login(request: Request):
    """Start Slack OAuth flow."""
    org_id, user_id = extract_context_from_cookie(request)
    state = secrets.token_urlsafe(32)

    query = urlencode(
        {
            "client_id": settings.slack_client_id,
            "redirect_uri": settings.slack_redirect_uri,
            "scope": "chat:write,chat:write.public,channels:read,channels:manage,channels:history,groups:read,groups:history,reactions:write,users:read,team:read",
            "state": state,
        }
    )

    response = RedirectResponse(
        url=f"https://slack.com/oauth/v2/authorize?{query}",
        status_code=302,
    )

    set_oauth_state_cookie(response, "slack", state, org_id, user_id)
    response.headers["Cache-Control"] = "no-store"
    return response


@router.get("/slack-test")
async def slack_test(claims: dict = Depends(verify_jwt)):
    """Quick Slack connectivity test using stored token."""
    org_id = claims["org"]
    token_doc = await SlackTokenDocument.find_one({"organization_id": org_id})

    if not token_doc:
        return {"error": "No Slack token in database. Please connect Slack first."}

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://slack.com/api/auth.test",
            headers={
                "Authorization": f"Bearer {token_doc.access_token}",
            },
        )

    return resp.json()


@router.get("/slack/callback")
async def slack_callback(
    request: Request,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
):
    """Slack OAuth callback."""

    if error:
        response = connector_redirect("slack", "denied")
        return response

    auth_state = await validate_oauth_state(request, "slack", state)
    
    print("========== SLACK CALLBACK DIAGNOSTIC ==========")
    print(f"Auth State Provider: {auth_state.provider}")
    print(f"Auth State Org ID: {auth_state.organization_id}")
    print(f"Auth State User ID: {auth_state.user_id}")
    print("===============================================")


    if not code:
        raise HTTPException(
            status_code=400,
            detail="Slack did not return an authorization code.",
        )

    async with httpx.AsyncClient(timeout=15.0) as client:
        token_response = await client.post(
            "https://slack.com/api/oauth.v2.access",
            data={
                "client_id": settings.slack_client_id,
                "client_secret": settings.slack_client_secret,
                "code": code,
                "redirect_uri": settings.slack_redirect_uri,
            },
        )

    token_data = token_response.json()

    print("========== SLACK TOKEN RESPONSE ==========")
    print(token_data)
    print("===========================================")

    if not token_response.is_success or not token_data.get("ok"):
        raise HTTPException(
            status_code=502,
            detail="Slack token exchange failed.",
        )

    access_token = token_data.get("access_token")
    team_name = token_data.get("team", {}).get("name", "Slack workspace")
    team_id = token_data.get("team", {}).get("id", "unknown")

    if not access_token:
        raise HTTPException(
            status_code=502,
            detail="Slack did not return an access token.",
        )

    # Upsert Slack token
    org_id = auth_state.organization_id
    user_id = auth_state.user_id

    existing = await SlackTokenDocument.find_one({
        "team_id": team_id,
        "organization_id": org_id,
    })

    if existing:
        existing.access_token = access_token
        existing.team_name = team_name
        if org_id:
            existing.organization_id = org_id
        if user_id:
            existing.user_id = user_id
        await existing.save()
        print("Slack token updated in MongoDB")
    else:
        await SlackTokenDocument(
            team_id=team_id,
            team_name=team_name,
            access_token=access_token,
            organization_id=org_id,
            user_id=user_id,
        ).insert()
        print("Slack token inserted into MongoDB")

    print(f"Slack connected: {team_name} ({team_id})")

    response = connector_redirect("slack", "connected")
    return response


# ===================================================================
# Google OAuth
# Google OAuth uses the SAME cookie-based state mechanism as GitHub/Slack.
# The old in-memory GOOGLE_OAUTH_STATES dict is removed.
# ===================================================================

@router.get("/google")
async def google_login(request: Request):
    """
    Start Google OAuth flow for Gmail + Calendar + Sheets.

    Uses cookie-based state (same as GitHub and Slack) to prevent CSRF.
    """
    org_id, user_id = extract_context_from_cookie(request)

    if not settings.google_client_id:
        raise HTTPException(
            status_code=500,
            detail="GOOGLE_CLIENT_ID is not configured.",
        )

    if not settings.google_client_secret:
        raise HTTPException(
            status_code=500,
            detail="GOOGLE_CLIENT_SECRET is not configured.",
        )

    if not settings.google_redirect_uri:
        raise HTTPException(
            status_code=500,
            detail="GOOGLE_REDIRECT_URI is not configured.",
        )

    # Generate state — stored in cookie, NOT in-memory dict.
    state = secrets.token_urlsafe(32)

    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": settings.google_redirect_uri,
        "response_type": "code",
        "scope": " ".join(GOOGLE_SCOPES),
        "access_type": "offline",
        "prompt": "consent",
        "state": state,
    }

    google_auth_url = f"{GOOGLE_AUTH_URL}?{urlencode(params)}"

    print("===========================================")
    print("GOOGLE OAUTH START")
    print(f"Client ID: {settings.google_client_id}")
    print(f"Redirect URI: {settings.google_redirect_uri}")
    print(f"State: {state}")
    print("===========================================")

    response = RedirectResponse(url=google_auth_url, status_code=302)

    # Set state in cookie — this is the FIX for the missing state problem
    set_oauth_state_cookie(response, "google", state, org_id, user_id)
    response.headers["Cache-Control"] = "no-store"

    return response


@router.get("/google/callback")
async def google_callback(
    request: Request,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
):
    """
    Google OAuth callback.

    Validates cookie state, exchanges code for tokens, fetches Google user
    info, then saves/upserts GoogleTokenDocument in MongoDB.
    """
    print("===========================================")
    print("GOOGLE OAUTH CALLBACK")
    print(f"Received state: {state!r}")
    print(f"Received code: {bool(code)}")
    print(f"Received error: {error}")
    print(f"All cookies: {dict(request.cookies)}")
    print("===========================================")

    if error:
        response = connector_redirect("google", "denied")
        return response

    # Validate state using server-side OAuthStateDocument
    auth_state = await validate_oauth_state(request, "google", state)

    if not code:
        raise HTTPException(
            status_code=400,
            detail="Google did not return an authorization code.",
        )

    # Exchange authorization code for tokens
    token_payload = {
        "client_id": settings.google_client_id,
        "client_secret": settings.google_client_secret,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": settings.google_redirect_uri,
    }

    async with httpx.AsyncClient(timeout=30.0) as client:

        token_response = await client.post(
            GOOGLE_TOKEN_URL,
            data=token_payload,
        )

    print(f"Google token response status: {token_response.status_code}")

    if token_response.status_code != 200:
        raise HTTPException(
            status_code=502,
            detail={
                "message": "Google token exchange failed.",
                "google_status": token_response.status_code,
                "google_response": token_response.text,
            },
        )

    tokens = token_response.json()

    access_token = tokens.get("access_token")
    refresh_token = tokens.get("refresh_token")
    expires_in = tokens.get("expires_in", 3600)
    scope = tokens.get("scope", "")

    if not access_token:
        raise HTTPException(
            status_code=502,
            detail="Google did not return an access token.",
        )

    # Calculate token expiry timestamp
    token_expiry = (
        datetime.now(timezone.utc) + timedelta(seconds=expires_in)
    ).timestamp()

    # Fetch Google user info (email)
    async with httpx.AsyncClient(timeout=15.0) as client:
        userinfo_response = await client.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )

    google_email = None
    if userinfo_response.status_code == 200:
        userinfo = userinfo_response.json()
        google_email = userinfo.get("email")
        print(f"Google user email: {google_email}")

    scopes_list = scope.split() if scope else []

    # Save/upsert GoogleTokenDocument in MongoDB
    # Upsert by google_email if available, otherwise by first record
    org_id = auth_state.organization_id
    user_id = auth_state.user_id

    existing = None
    if google_email:
        existing = await GoogleTokenDocument.find_one(
            {"google_email": google_email, "organization_id": org_id}
        )

    if existing:
        existing.access_token = access_token
        if refresh_token:
            existing.refresh_token = refresh_token
        existing.token_expiry = token_expiry
        existing.scopes = scopes_list
        if org_id:
            existing.organization_id = org_id
        if user_id:
            existing.user_id = user_id
        await existing.save()
        print(f"Google token updated for {google_email}")
    else:
        if not refresh_token:
            # If no refresh token (user already consented before), try to find any existing
            existing_any = await GoogleTokenDocument.find_one({"organization_id": org_id})
            if existing_any:
                existing_any.access_token = access_token
                existing_any.token_expiry = token_expiry
                existing_any.scopes = scopes_list
                if google_email:
                    existing_any.google_email = google_email
                if org_id:
                    existing_any.organization_id = org_id
                if user_id:
                    existing_any.user_id = user_id
                await existing_any.save()
                print("Google token updated (no new refresh token)")
            else:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "Google did not return a refresh token. "
                        "Please revoke access at https://myaccount.google.com/permissions "
                        "and try connecting again."
                    ),
                )
        else:
            await GoogleTokenDocument(
                google_email=google_email,
                access_token=access_token,
                refresh_token=refresh_token,
                token_expiry=token_expiry,
                scopes=scopes_list,
                organization_id=org_id,
                user_id=user_id,
            ).insert()
            print(f"Google token saved for {google_email}")

    print("===========================================")
    print("GOOGLE OAUTH SUCCESS")
    print(f"Email: {google_email}")
    print(f"Has refresh token: {bool(refresh_token)}")
    print("===========================================")

    response = connector_redirect("google", "connected")
    return response


@router.get("/google/test")
async def test_google_connection(claims: dict = Depends(verify_jwt)):
    """
    Test the stored Google OAuth connection by making a real API call.
    Imports the token service to auto-refresh if needed.
    """
    from syncsphere.connectors.application.google_token_service import (
        get_valid_google_token,
    )

    org_id = claims["org"]
    token_doc = await GoogleTokenDocument.find_one({"organization_id": org_id})

    if not token_doc:
        return JSONResponse(
            status_code=200,
            content={
                "provider": "google",
                "status": "not_connected",
                "connected": False,
                "message": "No Google account connected. Please connect Google first.",
            },
        )

    try:
        access_token = await get_valid_google_token(organization_id=org_id)

        # Verify by calling Google userinfo
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                GOOGLE_USERINFO_URL,
                headers={"Authorization": f"Bearer {access_token}"},
            )

        if resp.status_code != 200:
            return JSONResponse(
                content={
                    "provider": "google",
                    "status": "error",
                    "connected": False,
                    "message": "Google token is invalid. Please reconnect.",
                }
            )

        userinfo = resp.json()

        return {
            "provider": "google",
            "status": "connected",
            "connected": True,
            "email": userinfo.get("email"),
            "name": userinfo.get("name"),
            "services": {
                "gmail": True,
                "calendar": True,
                "sheets": True,
            },
            "message": "Google connection is healthy.",
        }

    except RuntimeError as exc:
        return JSONResponse(
            content={
                "provider": "google",
                "status": "error",
                "connected": False,
                "message": str(exc),
            }
        )