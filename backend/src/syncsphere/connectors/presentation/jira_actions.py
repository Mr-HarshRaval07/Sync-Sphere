"""
Jira Connector Actions
"""
import httpx
from typing import Any

from syncsphere.connectors.application.jira_token_service import (
    get_valid_jira_token,
    get_jira_connection_details
)
from syncsphere.connectors.application.exceptions import OAuthError

async def _get_jira_base_url(user_id: str, organization_id: str | None = None) -> tuple[str, str]:
    details = await get_jira_connection_details(user_id, organization_id)
    if not details or not details.get("cloud_id"):
        raise OAuthError("Jira site connection details missing. Please reconnect Jira.")
    
    # Using the native api.atlassian.com/ex/jira/{cloud_id} proxy for 3LO tokens
    base_url = f"https://api.atlassian.com/ex/jira/{details['cloud_id']}/rest/api/3"
    site_url = details["site_url"]
    return base_url, site_url

async def _lookup_project(token: str, base_url: str, project_key: str | None = None) -> str:
    """Validate or dynamically select a Jira project key before execution."""
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
    
    async with httpx.AsyncClient(timeout=15.0) as client:
        res = await client.get(f"{base_url}/project/search", headers=headers)
        
    if res.status_code != 200:
        if res.status_code in (401, 403):
             raise OAuthError("Jira permission error. Please reconnect your account.")
        raise RuntimeError("Failed to fetch Jira projects.")

    data = res.json()
    projects = data.get("values", [])
    
    if not projects:
        raise ValueError("No Jira projects found in your account. Please create a project in Jira first.")
        
    if project_key:
        matched = [p for p in projects if p.get("key") == project_key]
        if matched:
            return matched[0]["key"]
            
        if len(projects) == 1:
            return projects[0]["key"]
            
        err = f"Jira project '{project_key}' does not exist. Available projects: {', '.join([p['key'] for p in projects])}"
        raise ValueError(err)
        
    if len(projects) == 1:
        return projects[0]["key"]
        
    keys = [p["key"] for p in projects]
    raise ValueError(f"Multiple Jira projects found ({', '.join(keys)}). Please specify a valid project_key in the UI.")

async def create_issue(
    project_key: str,
    summary: str,
    issue_type: str = "Task",
    description: str | None = None,
    user_id: str | None = None,
    organization_id: str | None = None,
    **kwargs,
) -> dict[str, Any]:
    if not user_id:
        raise OAuthError("user_id is missing, cannot execute Jira action.")

    token = await get_valid_jira_token(user_id, organization_id)
    base_url, site_url = await _get_jira_base_url(user_id, organization_id)
    
    # Auto-resolve or validate project_key before creating issue
    try:
        project_key = await _lookup_project(token, base_url, project_key)
    except ValueError as e:
        raise ValueError(str(e))
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    payload = {
        "fields": {
            "project": {"key": project_key},
            "summary": summary,
            "issuetype": {"name": issue_type},
        }
    }
    
    # Jira REST v3 requires Atlassian Document Format (ADF) for description
    if description:
        payload["fields"]["description"] = {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [
                        {
                            "type": "text",
                            "text": description
                        }
                    ]
                }
            ]
        }

    async with httpx.AsyncClient(timeout=30.0) as client:
        res = await client.post(f"{base_url}/issue", headers=headers, json=payload)
        
    if res.status_code not in (200, 201):
        raise RuntimeError(f"Jira API error ({res.status_code}): {res.text}")
        
    data = res.json()
    issue_key = data.get("key")
    issue_url = f"{site_url}/browse/{issue_key}" if site_url and issue_key else None
        
    return {
        "status": "success",
        "issue_id": data.get("id"),
        "issue_key": issue_key,
        "issue_url": issue_url,
    }


async def update_issue(
    issue_key_or_id: str,
    summary: str | None = None,
    description: str | None = None,
    user_id: str | None = None,
    organization_id: str | None = None,
    **kwargs,
) -> dict[str, Any]:
    if not user_id:
        raise OAuthError("user_id is missing.")

    token = await get_valid_jira_token(user_id, organization_id)
    base_url, site_url = await _get_jira_base_url(user_id, organization_id)
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    fields_update = {}
    if summary:
        fields_update["summary"] = summary
    if description:
        fields_update["description"] = {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": description}]
                }
            ]
        }
        
    # Only make payload if there are fields to update
    if not fields_update:
        return {"status": "success", "message": "No fields to update."}

    payload = {"fields": fields_update}

    async with httpx.AsyncClient(timeout=30.0) as client:
        res = await client.put(f"{base_url}/issue/{issue_key_or_id}", headers=headers, json=payload)
        
    if res.status_code not in (200, 204):
        raise RuntimeError(f"Jira API error ({res.status_code}): {res.text}")
        
    return {
        "status": "success",
        "message": f"Issue {issue_key_or_id} updated successfully.",
        "issue_url": f"{site_url}/browse/{issue_key_or_id}" if site_url else None
    }


async def add_comment(
    issue_key_or_id: str,
    body: str,
    user_id: str | None = None,
    organization_id: str | None = None,
    **kwargs,
) -> dict[str, Any]:
    if not user_id:
        raise OAuthError("user_id is missing.")

    token = await get_valid_jira_token(user_id, organization_id)
    base_url, site_url = await _get_jira_base_url(user_id, organization_id)
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    payload = {
        "body": {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": body}]
                }
            ]
        }
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        res = await client.post(f"{base_url}/issue/{issue_key_or_id}/comment", headers=headers, json=payload)
        
    if res.status_code not in (200, 201):
        raise RuntimeError(f"Jira API error ({res.status_code}): {res.text}")
        
    data = res.json()
    return {
        "status": "success",
        "comment_id": data.get("id"),
        "issue_url": f"{site_url}/browse/{issue_key_or_id}" if site_url else None
    }


async def search_issues(
    jql: str,
    max_results: int = 10,
    user_id: str | None = None,
    organization_id: str | None = None,
    **kwargs,
) -> dict[str, Any]:
    if not user_id:
        raise OAuthError("user_id is missing.")

    token = await get_valid_jira_token(user_id, organization_id)
    base_url, site_url = await _get_jira_base_url(user_id, organization_id)
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json"
    }

    params = {
        "jql": jql,
        "maxResults": max_results,
        "fields": "summary,status,priority,assignee"
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        res = await client.get(f"{base_url}/search", headers=headers, params=params)
        
    if res.status_code != 200:
        raise RuntimeError(f"Jira API error ({res.status_code}): {res.text}")
        
    data = res.json()
    issues = []
    
    for issue in data.get("issues", []):
        fields = issue.get("fields", {})
        issues.append({
            "key": issue.get("key"),
            "summary": fields.get("summary"),
            "status": fields.get("status", {}).get("name"),
            "url": f"{site_url}/browse/{issue.get('key')}" if site_url else None
        })
        
    return {
        "status": "success",
        "total": data.get("total", 0),
        "issues": issues,
    }


async def get_issue(
    issue_key_or_id: str,
    user_id: str | None = None,
    organization_id: str | None = None,
    **kwargs,
) -> dict[str, Any]:
    if not user_id:
        raise OAuthError("user_id is missing.")

    token = await get_valid_jira_token(user_id, organization_id)
    base_url, site_url = await _get_jira_base_url(user_id, organization_id)
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json"
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        res = await client.get(f"{base_url}/issue/{issue_key_or_id}", headers=headers)
        
    if res.status_code != 200:
        raise RuntimeError(f"Jira API error ({res.status_code}): {res.text}")
        
    data = res.json()
    fields = data.get("fields", {})
    
    return {
        "status": "success",
        "key": data.get("key"),
        "summary": fields.get("summary"),
        "issue_type": fields.get("issuetype", {}).get("name"),
        "issue_status": fields.get("status", {}).get("name"),
        "assignee": fields.get("assignee", {}).get("displayName"),
        "url": f"{site_url}/browse/{data.get('key')}" if site_url else None
    }
