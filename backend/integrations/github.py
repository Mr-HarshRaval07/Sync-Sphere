import os
import requests

try:
    from backend.config import (
        GITHUB_TOKEN,
        GITHUB_OWNER,
        GITHUB_REPO,
    )
except ModuleNotFoundError:
    from config import (
        GITHUB_TOKEN,
        GITHUB_OWNER,
        GITHUB_REPO,
    )


def create_github_issue(title: str, assigned_to: str, status: str = "Pending"):
    """
    Creates a GitHub Issue in the configured repository.
    """

    token = (GITHUB_TOKEN or os.getenv("GITHUB_TOKEN") or "").strip()
    owner = (GITHUB_OWNER or os.getenv("GITHUB_OWNER") or "").strip()
    repo = (GITHUB_REPO or os.getenv("GITHUB_REPO") or "").strip()

    if not token:
        return {
            "ok": False,
            "error": "Missing GitHub Token"
        }

    if not owner or not repo:
        return {
            "ok": False,
            "error": "Missing repository information"
        }

    url = f"https://api.github.com/repos/{owner}/{repo}/issues"

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json"
    }

    body = f"""
## New Task

**Assigned To:** {assigned_to}

**Status:** {status}

---
Created automatically from Sync Sphere.
"""

    payload = {
        "title": title,
        "body": body
    }

    response = requests.post(
        url,
        headers=headers,
        json=payload,
        timeout=10
    )

    result = response.json()

    print("GitHub Response:", result)

    return result