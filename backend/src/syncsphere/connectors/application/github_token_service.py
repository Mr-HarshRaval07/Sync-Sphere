"""
GitHub Token Service

Provides GitHub OAuth access token validation and resolution.
Used by the AI Planner preflight checks and tasks router to ensure tokens exist.
"""
from syncsphere.tasks.documents import GitHubTokenDocument
from syncsphere.core.config.settings import settings
from syncsphere.connectors.application.exceptions import OAuthError


async def get_valid_github_token(
    organization_id: str | None = None,
    requested_account: str | None = None,
    user_id: str | None = None,
) -> str:
    """
    Return a valid GitHub access token.

    Lookup strictly enforces User-level isolation if a user_id is provided,
    to ensure users only access their own GitHub connections.

    Raises OAuthError if no token is found.
    """
    token_doc: GitHubTokenDocument | None = None

    if not user_id:
        raise OAuthError(
            "Authentication required. Cannot execute GitHub actions without an authenticated user."
        )

    if requested_account:
        token_doc = await GitHubTokenDocument.find_one({
            "github_username": {"$regex": f"^{requested_account}$", "$options": "i"},
            "user_id": user_id,
            "organization_id": organization_id
        })
        if not token_doc:
            raise OAuthError(
                f"Requested GitHub account '{requested_account}' is not authorized for your user. "
                "Please connect it at /dashboard/connectors."
            )
    else:
        token_doc = await GitHubTokenDocument.find_one({
            "user_id": user_id, 
            "organization_id": organization_id
        })

    if not token_doc:
        raise OAuthError(
            "No GitHub account connected. "
            "Please connect GitHub at /dashboard/connectors."
        )

    # Note: GitHub OAuth tokens created historically did not always expire
    # depending on App settings (fine-grained vs classic vs standard oauth app).
    # Since we aren't saving refresh tokens for GitHub in GitHubTokenDocument,
    # we assume the access token is valid until it gets a 401 locally from GitHub API.

    return token_doc.access_token
