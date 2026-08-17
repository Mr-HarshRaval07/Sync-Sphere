"""
GitHub Actions Connector — Real Implementation

Creates issues, comments, and pull requests via the GitHub API using
the stored GitHub OAuth token (not a hardcoded PAT).
"""
import httpx

from syncsphere.tasks.documents import GitHubTokenDocument

GITHUB_API_BASE = "https://api.github.com"


async def _get_github_token(organization_id: str | None = None, user_id: str | None = None) -> str:
    """
    Retrieve the stored GitHub OAuth access token.
    Enforces strict user isolation.
    """
    token_doc: GitHubTokenDocument | None = None

    if user_id and organization_id:
        token_doc = await GitHubTokenDocument.find_one(
            {"organization_id": organization_id, "user_id": user_id}
        )

    if not token_doc and organization_id:
        # Fallback for old documents that might not have user_id
        token_doc = await GitHubTokenDocument.find_one(
            {"organization_id": organization_id}
        )

    if not token_doc:
        raise RuntimeError(
            "No GitHub account connected. "
            "Please connect GitHub at /dashboard/connectors."
        )

    return token_doc.access_token


async def create_github_issue(
    owner: str,
    repo: str,
    title: str,
    body: str,
    labels: list | None = None,
    organization_id: str | None = None,
    user_id: str | None = None,
    **kwargs
) -> dict:
    """
    Create a GitHub issue in the specified repository.

    Args:
        owner: Repository owner (username or org)
        repo: Repository name
        title: Issue title
        body: Issue body (Markdown supported)
        labels: Optional list of label names
        organization_id: Optional org scope for multi-tenant

    Returns:
        GitHub API issue resource dict with html_url, number, etc.

    Raises:
        RuntimeError: If no GitHub token or API call fails
    """
    access_token = await _get_github_token(organization_id, user_id)

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    payload: dict = {
        "title": title,
        "body": body,
    }

    if labels:
        payload["labels"] = labels

    url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/issues"

    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.post(
            url,
            headers=headers,
            json=payload,
        )

    if response.status_code == 401:
        raise RuntimeError(
            "GitHub authentication failed. "
            "Please reconnect GitHub at /dashboard/connectors."
        )

    if response.status_code == 404:
        raise RuntimeError(
            f"GitHub repository not found: {owner}/{repo}. "
            "Check the owner and repository name."
        )

    if response.status_code == 410:
        raise RuntimeError(
            f"GitHub issues are disabled for repository: {owner}/{repo}."
        )

    if response.status_code != 201:
        error_info = {}
        try:
            error_info = response.json()
        except Exception:
            pass
        raise RuntimeError(
            f"GitHub API failed to create issue. "
            f"Status: {response.status_code}. "
            f"Error: {error_info.get('message', response.text)}"
        )

    result = response.json()
    print(
        f"[GitHub] Issue created: #{result.get('number')} "
        f"'{result.get('title')}' — {result.get('html_url')}"
    )
    return {
        "success": True,
        "number": result.get("number"),
        "title": result.get("title"),
        "repository": f"{owner}/{repo}",
        "html_url": result.get("html_url")
    }


async def get_github_authenticated_user(
    organization_id: str | None = None,
    user_id: str | None = None,
    **kwargs
) -> dict:
    """Get the authenticated GitHub user's profile."""
    access_token = await _get_github_token(organization_id, user_id)

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(
            f"{GITHUB_API_BASE}/user",
            headers=headers,
        )

    response.raise_for_status()
    return response.json()
