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
    JiraTokenDocument,
    NotionTokenDocument,
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
# Jira OAuth Configuration
# -------------------------------------------------------------------

JIRA_AUTH_URL = "https://auth.atlassian.com/authorize"
JIRA_TOKEN_URL = "https://auth.atlassian.com/oauth/token"
JIRA_ACCESSIBLE_RESOURCES_URL = "https://api.atlassian.com/oauth/token/accessible-resources"

JIRA_SCOPES = [
    "read:jira-work",
    "read:jira-user",
    "write:jira-work",
    "read:me",
    "read:account",
    "offline_access",
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
    requested_account: str | None = None
) -> None:
    """Store raw OAuth state securely in MongoDB."""
    expires_at = datetime.utcnow() + timedelta(seconds=OAUTH_STATE_MAX_AGE_SECONDS)
    await OAuthStateDocument(
        state=state,
        provider=provider,
        user_id=user_id,
        organization_id=org_id,
        requested_account=requested_account,
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
        
    if datetime.utcnow() > doc.expires_at:
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
    request: Request,
    claims: dict = Depends(verify_jwt),
):
    """
    Initialize an OAuth flow securely.
    The frontend calls this with a Bearer token (JWT).
    We generate a state, store it server-side, and return the auth URL.
    """
    try:
        body = await request.json() if request.headers.get("content-type") == "application/json" else {}
        requested_account = body.get("requested_account")
        
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
        elif provider == "jira":
            if not settings.jira_client_id or not settings.jira_client_secret or not settings.jira_redirect_uri:
                print("Jira OAuth configuration is incomplete.")
                raise HTTPException(status_code=500, detail="Jira OAuth configuration is incomplete.")

            params = {
                "audience": "api.atlassian.com",
                "client_id": settings.jira_client_id,
                "scope": " ".join(JIRA_SCOPES),
                "redirect_uri": settings.jira_redirect_uri,
                "state": state,
                "response_type": "code",
                "prompt": "consent",
            }
            
            # Log safely for debugging App ID issues
            print("========== JIRA OAUTH CONFIG DIAGNOSTIC ==========")
            print(f"Jira Client ID: {settings.jira_client_id}")
            print(f"Jira Redirect URI: {settings.jira_redirect_uri}")
            print(f"Jira Response Type: code")
            print(f"Jira Scopes: {' '.join(JIRA_SCOPES)}")
            print("==================================================")
            
            auth_url = f"{JIRA_AUTH_URL}?{urlencode(params)}"
        elif provider == "notion":
            params = {
                "client_id": settings.notion_client_id,
                "redirect_uri": settings.notion_redirect_uri,
                "response_type": "code",
                "owner": "user",
                "state": state,
            }
            auth_url = f"{settings.notion_auth_url}?{urlencode(params)}"
        else:
            raise HTTPException(status_code=400, detail="Unknown provider")
            
        await create_oauth_state_document(provider, state, org_id, user_id, requested_account)
        return {"auth_url": auth_url}
    except HTTPException:
        raise
    except Exception as exc:
        import traceback
        tb = traceback.format_exc()
        import logging
        logging.getLogger(__name__).exception("Jira OAuth initiation failed")
        raise HTTPException(status_code=500, detail=f"Jira OAuth initiation failed: {str(exc)}\n{tb}")


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
    google_token = await GoogleTokenDocument.find_one({"organization_id": org_id, "user_id": claims.get("sub")})
    google_status: dict = {"connected": False}
    if google_token:
        google_status = {
            "connected": True,
            "email": google_token.google_email,
        }

    # GitHub
    github_token = await GitHubTokenDocument.find_one({"organization_id": org_id, "user_id": claims.get("sub")})
    github_status: dict = {"connected": False}
    if github_token:
        github_status = {
            "connected": True,
            "username": github_token.github_username,
        }
        
    # Jira
    jira_token = await JiraTokenDocument.find_one({"organization_id": org_id, "user_id": claims["sub"]})
    jira_status: dict = {"connected": False}
    if jira_token:
        jira_status = {
            "connected": True,
            "site_name": jira_token.site_name,
            "site_url": jira_token.site_url,
        }

    # Slack
    slack_token = await SlackTokenDocument.find_one({"organization_id": org_id, "user_id": claims.get("sub")})
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

    # Notion
    notion_token = await NotionTokenDocument.find_one({"organization_id": org_id, "user_id": claims.get("sub")})
    notion_status: dict = {"connected": False}
    if notion_token:
        notion_status = {
            "connected": True,
            "workspace_name": notion_token.workspace_name,
            "workspace_icon": notion_token.workspace_icon,
            "default_parent_id": getattr(notion_token, "default_parent_id", None),
            "default_parent_type": getattr(notion_token, "default_parent_type", None)
        }

    return JSONResponse({
        "google": google_status,
        "github": github_status,
        "slack": slack_status,
        "jira": jira_status,
        "notion": notion_status,
    })


# ===================================================================
# POST /v1/connect/slack/disconnect
# ===================================================================

@router.post("/slack/disconnect")
async def disconnect_slack(claims: dict = Depends(verify_jwt)):
    org_id = claims["org"]
    token_doc = await SlackTokenDocument.find_one({"organization_id": org_id, "user_id": claims.get("sub")})
    if token_doc:
        try:
            async with httpx.AsyncClient() as client:
                await client.post(
                    "https://slack.com/api/auth.revoke",
                    headers={"Authorization": f"Bearer {token_doc.access_token}"}
                )
        except Exception as e:
            print(f"Error revoking Slack token: {e}")
        await token_doc.delete()
    return {"status": "success"}


# ===================================================================
# POST /v1/connect/google/disconnect
# ===================================================================

@router.post("/google/disconnect")
async def disconnect_google(claims: dict = Depends(verify_jwt)):
    org_id = claims["org"]
    token_doc = await GoogleTokenDocument.find_one({"organization_id": org_id, "user_id": claims.get("sub")})
    if token_doc:
        try:
            async with httpx.AsyncClient() as client:
                await client.post(
                    "https://oauth2.googleapis.com/revoke",
                    params={"token": token_doc.access_token},
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                )
        except Exception as e:
            print(f"Error revoking Google token: {e}")
        await token_doc.delete()
    return {"status": "success"}


# ===================================================================
# POST /v1/connect/github/disconnect
# ===================================================================

@router.post("/github/disconnect")
async def disconnect_github(claims: dict = Depends(verify_jwt)):
    org_id = claims["org"]
    user_id = claims.get("sub")
    
    # Try fully scoped first
    token_doc = await GitHubTokenDocument.find_one({
        "organization_id": org_id,
        "user_id": user_id
    })
        
    if token_doc:
        # GitHub OAuth token revocation via API might not be fully supported here,
        # handling local disconnect by deleting the DB record.
        await token_doc.delete()
        print(f"GitHub token locally revoked for {token_doc.github_username}")

    return {"status": "success"}


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
        {"github_username": github_username, "organization_id": org_id, "user_id": user_id}
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
    token_doc = await SlackTokenDocument.find_one({"organization_id": org_id, "user_id": claims.get("sub")})

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
        "user_id": user_id,
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
    # The /google GET endpoint is legacy and doesn't get requested_account via body.

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

    # Enforce strict requested_account OAuth identity matching
    if google_email and auth_state.requested_account:
        if google_email.lower() != auth_state.requested_account.lower():
            raise HTTPException(
                status_code=400,
                detail=f"Account mismatch. You authorized {google_email}, but this action requires {auth_state.requested_account}. Please sign in with the correct account."
            )

    scopes_list = scope.split() if scope else []

    # Save/upsert GoogleTokenDocument in MongoDB
    # Upsert by google_email if available, otherwise by first record
    org_id = auth_state.organization_id
    user_id = auth_state.user_id

    existing = None
    if google_email:
        existing = await GoogleTokenDocument.find_one(
            {"google_email": google_email, "organization_id": org_id, "user_id": user_id}
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
            # If no refresh token (user already consented before), try to find any existing for THIS user
            existing_any = await GoogleTokenDocument.find_one({"organization_id": org_id, "user_id": user_id})
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
    user_id = claims.get("sub")
    token_doc = await GoogleTokenDocument.find_one({"organization_id": org_id, "user_id": user_id})

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
        access_token = await get_valid_google_token(organization_id=org_id, user_id=user_id)

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

# ===================================================================
# GET /v1/connect/jira
# ===================================================================

@router.get("/jira")
async def jira_login(request: Request):
    """Start Jira OAuth flow — redirects browser directly to Atlassian authorization page."""
    org_id, user_id = extract_context_from_cookie(request)

    if not settings.jira_client_id or not settings.jira_client_secret or not settings.jira_redirect_uri:
        raise HTTPException(
            status_code=500,
            detail="Jira OAuth configuration is incomplete. Ensure JIRA_CLIENT_ID, JIRA_CLIENT_SECRET, and JIRA_REDIRECT_URI are set.",
        )

    state = secrets.token_urlsafe(32)

    params = {
        "audience": "api.atlassian.com",
        "client_id": settings.jira_client_id,
        "scope": " ".join(JIRA_SCOPES),
        "redirect_uri": settings.jira_redirect_uri,
        "state": state,
        "response_type": "code",
        "prompt": "consent",
    }

    print("========== JIRA OAUTH INITIATION (GET /jira) ==========")
    print(f"Jira Client ID: {settings.jira_client_id}")
    print(f"Jira Redirect URI: {settings.jira_redirect_uri}")
    print(f"Jira Scopes: {' '.join(JIRA_SCOPES)}")
    print("=======================================================")

    auth_url = f"{JIRA_AUTH_URL}?{urlencode(params)}"

    await create_oauth_state_document("jira", state, org_id, user_id)

    response = RedirectResponse(url=auth_url, status_code=302)
    response.headers["Cache-Control"] = "no-store"
    return response


# ===================================================================
# POST /v1/connect/jira/disconnect
# ===================================================================

@router.post("/jira/disconnect")
async def disconnect_jira(claims: dict = Depends(verify_jwt)):
    org_id = claims["org"]
    user_id = claims["sub"]
    token_doc = await JiraTokenDocument.find_one({"organization_id": org_id, "user_id": user_id})
    if token_doc:
        await token_doc.delete()
    return {"status": "success"}

# ===================================================================
# GET /v1/connect/jira/callback
# ===================================================================

@router.get("/jira/callback")
async def jira_callback(
    request: Request,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
):
    if error:
        return connector_redirect("jira", f"error: {error}")

    try:
        auth_state = await validate_oauth_state(request, "jira", state)

        if not code:
            raise HTTPException(status_code=400, detail="Jira did not return an authorization code.")

        if not settings.jira_client_id or not settings.jira_client_secret or not settings.jira_redirect_uri:
            print("Jira OAuth configuration is incomplete.")
            raise HTTPException(status_code=500, detail="Jira OAuth configuration is incomplete.")

        token_payload = {
            "client_id": settings.jira_client_id,
            "client_secret": settings.jira_client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": settings.jira_redirect_uri,
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            token_response = await client.post(JIRA_TOKEN_URL, json=token_payload)

        if token_response.status_code != 200:
            raise HTTPException(
                status_code=502,
                detail={
                    "message": "Jira token exchange failed.",
                    "jira_status": token_response.status_code,
                    "jira_response": token_response.text,
                },
            )

        tokens = token_response.json()
        access_token = tokens.get("access_token")
        refresh_token = tokens.get("refresh_token")
        try:
            expires_in = int(tokens.get("expires_in") or 3600)
        except ValueError:
            expires_in = 3600

        if not access_token:
            raise HTTPException(status_code=502, detail="Jira did not return an access token.")

        token_expiry = datetime.utcnow() + timedelta(seconds=expires_in)

        cloud_id = None
        site_name = None
        site_url = None
        account_id = None

        # Jira requires a secondary request to `accessible-resources` to get the Cloud ID (site)
        async with httpx.AsyncClient(timeout=15.0) as client:
            resources_response = await client.get(
                JIRA_ACCESSIBLE_RESOURCES_URL,
                headers={"Authorization": f"Bearer {access_token}"},
            )
            
            # Identify the connected Atlassian account
            me_response = await client.get(
                "https://api.atlassian.com/me",
                headers={"Authorization": f"Bearer {access_token}"}
            )

        if resources_response.status_code == 200:
            try:
                resources = resources_response.json()
                if isinstance(resources, list) and len(resources) > 0:
                    first_resource = resources[0]
                    if isinstance(first_resource, dict):
                        cloud_id = first_resource.get("id")
                        site_name = first_resource.get("name")
                        site_url = first_resource.get("url")
            except Exception as e:
                print(f"Failed to parse Atlassian resources response: {e}")
                
        if me_response.status_code == 200:
            try:
                me_data = me_response.json()
                account_id = me_data.get("account_id")
            except Exception as e:
                print(f"Failed to parse Atlassian /me response: {e}")

        if not cloud_id:
            raise HTTPException(status_code=502, detail="No Jira accessible resources found. Ensure your Atlassian account has a Jira site.")

        org_id = auth_state.organization_id
        user_id = auth_state.user_id

        existing = await JiraTokenDocument.find_one({
            "organization_id": org_id,
            "user_id": user_id, 
            "cloud_id": cloud_id
        })

        if existing:
            existing.access_token = access_token
            if refresh_token:
                existing.refresh_token = refresh_token
            existing.expires_at = token_expiry
            existing.site_name = site_name
            existing.site_url = site_url
            existing.account_id = account_id
            await existing.save()
        else:
            await JiraTokenDocument(
                organization_id=org_id,
                user_id=user_id,
                access_token=access_token,
                refresh_token=refresh_token,
                expires_at=token_expiry,
                cloud_id=cloud_id,
                site_name=site_name,
                site_url=site_url,
                account_id=account_id,
            ).insert()

        return connector_redirect("jira", "connected")

    except HTTPException:
        raise
    except Exception as exc:
        import traceback
        tb = traceback.format_exc()
        import logging
        logging.getLogger(__name__).exception("Jira Callback failed")
        raise HTTPException(status_code=500, detail=f"Jira Callback failed: {str(exc)}\n{tb}")

# ===================================================================
# GET /v1/connect/jira/projects
# ===================================================================

@router.get("/jira/projects")
async def get_jira_projects(claims: dict = Depends(verify_jwt)):
    """Fetch available Jira projects for the connected user."""
    org_id = claims["org"]
    user_id = claims["sub"]
    
    from syncsphere.connectors.application.jira_token_service import get_valid_jira_token, get_jira_connection_details
    try:
        token = await get_valid_jira_token(user_id, org_id)
        details = await get_jira_connection_details(user_id, org_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
        
    if not details or not details.get("cloud_id"):
        raise HTTPException(status_code=400, detail="Jira site connection configuration is missing.")
        
    base_url = f"https://api.atlassian.com/ex/jira/{details['cloud_id']}/rest/api/3"
    
    async with httpx.AsyncClient(timeout=15.0) as client:
        res = await client.get(
            f"{base_url}/project/search", 
            headers={"Authorization": f"Bearer {token}", "Accept": "application/json"}
        )
        if res.status_code != 200:
            raise HTTPException(status_code=res.status_code, detail=f"Failed to fetch Jira projects: {res.text}")
            
    data = res.json()
    return JSONResponse({"projects": data.get("values", [])})


# ===================================================================
# POST /v1/connect/notion/disconnect
# ===================================================================

@router.post("/notion/disconnect")
async def disconnect_notion(claims: dict = Depends(verify_jwt)):
    org_id = claims["org"]
    token_doc = await NotionTokenDocument.find_one({"organization_id": org_id, "user_id": claims.get("sub")})
    if not token_doc:
        token_doc = await NotionTokenDocument.find_one({"organization_id": org_id})
    if token_doc:
        # Notion doesn't have an automated revocation URL natively documented similarly, 
        # so we just drop the token from our DB.
        await token_doc.delete()
    return {"status": "success"}


# ===================================================================
# GET /v1/connect/notion
# ===================================================================

@router.get("/notion")
async def notion_login(request: Request):
    """Start Notion OAuth flow."""
    org_id, user_id = extract_context_from_cookie(request)
    state = secrets.token_urlsafe(32)

    params = {
        "client_id": settings.notion_client_id,
        "redirect_uri": settings.notion_redirect_uri,
        "response_type": "code",
        "owner": "user",
        "state": state,
    }

    response = RedirectResponse(
        url=f"{settings.notion_auth_url}?{urlencode(params)}",
        status_code=302,
    )

    # Notion auth doesn't support state validation easily through their redirect on legacy integrations, 
    # but we store state to match the architecture.
    set_oauth_state_cookie(response, "notion", state, org_id, user_id)
    return response


# ===================================================================
# GET /v1/connect/notion/callback
# ===================================================================

@router.get("/notion/callback")
async def notion_callback(
    request: Request,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
):
    """Notion OAuth callback."""

    if error:
        return connector_redirect("notion", "denied")

    auth_state = await validate_oauth_state(request, "notion", state)

    if not code:
        raise HTTPException(
            status_code=400,
            detail="Notion did not return an authorization code.",
        )

    import base64
    auth_string = f"{settings.notion_client_id}:{settings.notion_client_secret}"
    b64_auth = base64.b64encode(auth_string.encode("utf-8")).decode("utf-8")

    async with httpx.AsyncClient(timeout=15.0) as client:
        token_response = await client.post(
            settings.notion_token_url,
            headers={
                "Authorization": f"Basic {b64_auth}",
                "Content-Type": "application/json",
            },
            json={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": settings.notion_redirect_uri,
            }
        )

    if token_response.status_code != 200:
        raise HTTPException(
            status_code=502,
            detail="Notion token exchange failed.",
        )

    token_data = token_response.json()
    
    access_token = token_data.get("access_token")
    workspace_id = token_data.get("workspace_id")
    workspace_name = token_data.get("workspace_name")
    workspace_icon = token_data.get("workspace_icon")
    bot_id = token_data.get("bot_id")
    owner = token_data.get("owner", {}).get("user", {}).get("id") or "user"
    duplicated_template_id = token_data.get("duplicated_template_id")
    token_type = token_data.get("token_type")

    if not access_token or not workspace_id:
        raise HTTPException(
            status_code=502,
            detail="Notion did not return a valid access token or workspace ID.",
        )

    import logging
    async with httpx.AsyncClient(timeout=15.0) as verify_client:
        me_resp = await verify_client.get(
            "https://api.notion.com/v1/users/me",
            headers={"Authorization": f"Bearer {access_token}", "Notion-Version": "2022-06-28"}
        )
        
        all_results = []
        has_more = True
        next_cursor = None
        
        while has_more:
            payload = {"page_size": 100}
            if next_cursor:
                payload["start_cursor"] = next_cursor
                
            search_resp = await verify_client.post(
                "https://api.notion.com/v1/search",
                headers={"Authorization": f"Bearer {access_token}", "Notion-Version": "2022-06-28", "Content-Type": "application/json"},
                json=payload
            )
            
            if search_resp.status_code == 200:
                search_data = search_resp.json()
                all_results.extend(search_data.get("results", []))
                has_more = search_data.get("has_more", False)
                next_cursor = search_data.get("next_cursor")
            else:
                has_more = False
                logging.error(f"Notion Search API Pagination Error: {search_resp.text}")
    
    pages = [r for r in all_results if r.get("object") == "page"]
    databases = [r for r in all_results if r.get("object") == "database"]
    
    from syncsphere.tasks.documents import AccessiblePage
    accessible_pages_cache = []
    for item in all_results:
        title = "Untitled"
        if item.get("object") == "page":
            props = item.get("properties", {})
            for k, v in props.items():
                if v.get("type") == "title":
                    title_parts = v.get("title", [])
                    if title_parts:
                        title = title_parts[0].get("plain_text", "Untitled")
        elif item.get("object") == "database":
            title_parts = item.get("title", [])
            if title_parts:
                title = title_parts[0].get("plain_text", "Untitled")
                
        if item.get("object") in ["page", "database"]:
            accessible_pages_cache.append(AccessiblePage(id=item["id"], title=title, type=item.get("object")))
            
    logging.info("NOTION OAUTH VERIFICATION:")
    logging.info(f"- Workspace Name: {workspace_name}")
    logging.info(f"- Workspace ID: {workspace_id}")
    logging.info(f"- Owner Type: {owner}")
    logging.info(f"- Accessible Pages: {len(pages)}")
    logging.info(f"- Accessible Databases: {len(databases)}")

    if len(pages) == 0 and len(databases) == 0:
        raise HTTPException(
            status_code=400,
            detail="Notion OAuth succeeded, but no pages or databases are shared with this integration. Please open a page in Notion, click Share → Connections → SyncSphere Notion."
        )

    org_id = auth_state.organization_id
    user_id = auth_state.user_id

    # Upsert Notion token
    existing = await NotionTokenDocument.find_one({
        "workspace_id": workspace_id,
        "organization_id": org_id,
    })

    if existing:
        existing.access_token = access_token
        existing.workspace_name = workspace_name
        existing.workspace_icon = workspace_icon
        existing.bot_id = bot_id
        existing.owner = owner
        existing.duplicated_template_id = duplicated_template_id
        existing.token_type = token_type
        existing.accessible_pages = accessible_pages_cache
        if user_id:
            existing.user_id = user_id
        await existing.save()
        print("Notion token updated in MongoDB")
    else:
        await NotionTokenDocument(
            organization_id=org_id,
            user_id=user_id,
            workspace_id=workspace_id,
            workspace_name=workspace_name,
            workspace_icon=workspace_icon,
            access_token=access_token,
            bot_id=bot_id,
            owner=owner,
            duplicated_template_id=duplicated_template_id,
            token_type=token_type,
            accessible_pages=accessible_pages_cache,
        ).insert()
        print("Notion token inserted into MongoDB")
    return connector_redirect("notion", "connected")

# ===================================================================
# POST /v1/connect/notion/disconnect
# ===================================================================

@router.post("/notion/disconnect")
async def disconnect_notion(claims: dict = Depends(verify_jwt)):
    org_id = claims["org"]
    user_id = claims.get("sub")
    
    token_doc = await NotionTokenDocument.find_one({
        "organization_id": org_id,
        "user_id": user_id
    })
    
    if not token_doc:
        token_doc = await NotionTokenDocument.find_one({"organization_id": org_id})
        
    if token_doc:
        await token_doc.delete()
        print(f"Notion token locally revoked for {token_doc.workspace_name}")

    return {"status": "success"}

# ===================================================================
# POST /v1/connect/notion/test
# ===================================================================

from syncsphere.connectors.presentation.notion_actions import create_page

@router.post("/notion/test")
async def test_notion(claims: dict = Depends(verify_jwt)):
    org_id = claims["org"]
    user_id = claims.get("sub")
    
    token_doc = await NotionTokenDocument.find_one({
        "organization_id": org_id,
        "user_id": user_id
    })
    
    if not token_doc:
        token_doc = await NotionTokenDocument.find_one({"organization_id": org_id})
        
    if not token_doc:
        raise HTTPException(status_code=400, detail="Not connected")
        
    try:
        # Verify Token and Search API
        async with httpx.AsyncClient(timeout=15.0) as client:
            search_resp = await client.post(
                "https://api.notion.com/v1/search",
                headers={"Authorization": f"Bearer {token_doc.access_token}", "Notion-Version": "2022-06-28", "Content-Type": "application/json"},
                json={"page_size": 100}
            )
        if search_resp.status_code != 200:
            raise HTTPException(status_code=500, detail=f"Search API failed: {search_resp.text}")
            
        results = search_resp.json().get("results", [])
        pages = [r for r in results if r.get("object") == "page"]
        databases = [r for r in results if r.get("object") == "database"]
        
        return {
            "success": True,
            "oauth_token_valid": True,
            "search_api_works": True,
            "accessible_pages": len(pages),
            "accessible_databases": len(databases),
            "workspace_id": token_doc.workspace_id,
            "workspace_name": token_doc.workspace_name,
            "page_url": "https://notion.so/my-integrations" 
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ===================================================================
# GET /v1/connect/notion/accessible-pages
# ===================================================================

@router.get("/notion/accessible-pages")
async def get_notion_parents(claims: dict = Depends(verify_jwt)):
    org_id = claims["org"]
    user_id = claims.get("sub")
    
    token_doc = await NotionTokenDocument.find_one({
        "organization_id": org_id,
        "user_id": user_id
    })
    
    if not token_doc:
        token_doc = await NotionTokenDocument.find_one({"organization_id": org_id})
        
    if not token_doc:
        raise HTTPException(status_code=400, detail="Not connected")
        
    try:
        # Guarantee parent return uses the securely cached values
        # This completely resolves 404 object_not_found caused by missing top-20 search results in dynamically executed APIs.
        parents = []
        for p in getattr(token_doc, "accessible_pages", []):
            parents.append({
                "id": p.id,
                "title": p.title,
                "type": p.type
            })
            
        return parents
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
# ===================================================================
# PATCH /v1/connect/notion/parent
# ===================================================================

from pydantic import BaseModel

class UpdateNotionParentRequest(BaseModel):
    parent_id: str
    parent_type: str

@router.patch("/notion/parent")
async def set_notion_parent(request: UpdateNotionParentRequest, claims: dict = Depends(verify_jwt)):
    org_id = claims["org"]
    user_id = claims.get("sub")
    
    token_doc = await NotionTokenDocument.find_one({
        "organization_id": org_id,
        "user_id": user_id
    })
    
    if not token_doc:
        token_doc = await NotionTokenDocument.find_one({"organization_id": org_id})
        
    if not token_doc:
        raise HTTPException(status_code=400, detail="Not connected")
        
    token_doc.default_parent_id = request.parent_id
    token_doc.default_parent_type = request.parent_type
    
    await token_doc.save()
    
    return {"status": "success", "default_parent_id": token_doc.default_parent_id, "default_parent_type": token_doc.default_parent_type}


# ===================================================================
# POST /v1/connect/notion/refresh
# ===================================================================

@router.post("/notion/refresh")
async def refresh_notion_pages(claims: dict = Depends(verify_jwt)):
    org_id = claims["org"]
    user_id = claims.get("sub")
    
    token_doc = await NotionTokenDocument.find_one({
        "organization_id": org_id,
        "user_id": user_id
    })
    if not token_doc:
        token_doc = await NotionTokenDocument.find_one({"organization_id": org_id})
        
    if not token_doc:
        raise HTTPException(status_code=400, detail="Not connected")
        
    import logging
    async with httpx.AsyncClient(timeout=30.0) as verify_client:
        all_results = []
        has_more = True
        next_cursor = None
        
        while has_more:
            payload = {"page_size": 100}
            if next_cursor:
                payload["start_cursor"] = next_cursor
                
            search_resp = await verify_client.post(
                "https://api.notion.com/v1/search",
                headers={"Authorization": f"Bearer {token_doc.access_token}", "Notion-Version": "2022-06-28", "Content-Type": "application/json"},
                json=payload
            )
            
            if search_resp.status_code == 200:
                search_data = search_resp.json()
                all_results.extend(search_data.get("results", []))
                has_more = search_data.get("has_more", False)
                next_cursor = search_data.get("next_cursor")
            else:
                has_more = False
                logging.error(f"Notion Search API Pagination Error during refresh: {search_resp.text}")
    
    from syncsphere.tasks.documents import AccessiblePage
    accessible_pages_cache = []
    
    for item in all_results:
        title = "Untitled"
        if item.get("object") == "page":
            props = item.get("properties", {})
            for k, v in props.items():
                if v.get("type") == "title":
                    title_parts = v.get("title", [])
                    if title_parts:
                        title = title_parts[0].get("plain_text", "Untitled")
        elif item.get("object") == "database":
            title_parts = item.get("title", [])
            if title_parts:
                title = title_parts[0].get("plain_text", "Untitled")
                
        if item.get("object") in ["page", "database"]:
            accessible_pages_cache.append(AccessiblePage(id=item["id"], title=title, type=item.get("object")))
            
    token_doc.accessible_pages = accessible_pages_cache
    await token_doc.save()
    
    logging.info(f"NOTION REFRESH: Refreshed {len(accessible_pages_cache)} pages for {getattr(token_doc, 'workspace_name', 'Unknown')}.")
    return {"status": "success", "accessible_pages": len(accessible_pages_cache), "default_parent_type": token_doc.default_parent_type}
