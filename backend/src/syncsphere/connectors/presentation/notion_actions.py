"""
Notion Actions Connector — Real Implementation

Provides Notion document management actions by calling the Notion API
using the stored Notion OAuth access token.
"""
import httpx

from syncsphere.tasks.documents import NotionTokenDocument


NOTION_API_BASE = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"

async def _get_notion_doc(organization_id: str | None = None, user_id: str | None = None) -> NotionTokenDocument | None:
    token_doc = None
    if user_id and organization_id:
        token_doc = await NotionTokenDocument.find_one(
            {"organization_id": organization_id, "user_id": user_id}
        )
    if not token_doc and organization_id:
        token_doc = await NotionTokenDocument.find_one(
            {"organization_id": organization_id}
        )
    return token_doc

async def _get_notion_token(organization_id: str | None = None, user_id: str | None = None) -> str:
    """Retrieve the stored Notion OAuth access token."""
    token_doc = await _get_notion_doc(organization_id, user_id)

    if not token_doc:
        raise RuntimeError(
            "No Notion workspace connected. "
            "Please connect Notion at /dashboard/connectors."
        )

    return token_doc.access_token

def _get_headers(access_token: str) -> dict:
    return {
        "Authorization": f"Bearer {access_token}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json"
    }


def _build_rich_text(text: str) -> list:
    if not text: return []
    return [{"type": "text", "text": {"content": text}}]

def _blocks_from_markdown(markdown_text: str) -> list:
    """Fallback rudimentary text to blocks conversion."""
    if not markdown_text:
        return []
    
    blocks = []
    for paragraph in markdown_text.split('\n\n'):
        if not paragraph.strip(): continue
        blocks.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": _build_rich_text(paragraph.strip())
            }
        })
    return blocks

async def search_pages(
    search_text: str = "",
    organization_id: str | None = None,
    user_id: str | None = None,
    **kwargs
) -> dict:
    """Search for Notion pages or databases."""
    access_token = await _get_notion_token(organization_id, user_id)
    url = f"{NOTION_API_BASE}/search"
    
    payload = {
        "page_size": 20
    }
    if search_text:
        payload["query"] = search_text
    
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.post(url, headers=_get_headers(access_token), json=payload)
        
    if response.status_code != 200:
        raise RuntimeError(f"Notion API Search failed: {response.text}")
        
    data = response.json()
    results = []
    for item in data.get("results", []):
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
        
        results.append({
            "id": item["id"], 
            "title": title,
            "url": item.get("url"),
            "object": item.get("object")
        })
    return {"success": True, "results": results}

async def create_page(
    title: str,
    content: str = "",
    parent_id: str | None = None,
    parent_type: str | None = None,
    icon: str | None = None,
    cover: str | None = None,
    organization_id: str | None = None,
    user_id: str | None = None,
    **kwargs
) -> dict:
    """Create a Notion page."""
    # Resolve Token & Parent
    token_doc = await _get_notion_doc(organization_id, user_id)
    if not token_doc:
        raise RuntimeError("No Notion workspace connected.")
        
    access_token = token_doc.access_token
    
    # Logic: Strictly explicit from AI Planner / UI
    resolved_parent_id = parent_id
    resolved_parent_type = parent_type or "page"
    
    if not resolved_parent_id or not str(resolved_parent_id).strip():
        if user_id:
            from syncsphere.identity.infrastructure.documents.user_document import UserDocument
            user = await UserDocument.get(user_id)
            if user and hasattr(user, "preferences") and user.preferences:
                resolved_parent_id = user.preferences.default_notion_db_id
                resolved_parent_type = "database" # default to database if using fallback

    import logging
    logging.info(f"NOTION DEBUG: Verifying explicit parent {resolved_parent_id} of type {resolved_parent_type}")
    
    accessible_pages = getattr(token_doc, "accessible_pages", [])
    
    if not resolved_parent_id:
        raise RuntimeError(
            "Missing Notion target parent object! Please select a default Notion space in your connectors tab, "
            "or manually select a Parent Page ID in your automation configuration."
        )

    is_accessible = False
    parent_title = "Unknown"
    for p in accessible_pages:
        if p.id.replace("-", "") == resolved_parent_id.replace("-", ""):
            is_accessible = True
            resolved_parent_id = p.id
            resolved_parent_type = p.type
            parent_title = p.title
            break

    if not is_accessible:
        logging.warning(f"NOTION DEBUG: Parent {resolved_parent_id} is not accessible in cache. Attempting manual pass-through.")
        # Do not raise RuntimeError here anymore. User might be pasting a valid un-cached ID.
        
    logging.info(f"NOTION CONFIG:")
    logging.info(f"- Selected parent ID: {resolved_parent_id}")
    logging.info(f"- Parent title: {parent_title}")
    logging.info(f"- Object type: {resolved_parent_type}")
    logging.info(f"- OAuth workspace ID: {token_doc.workspace_id}")
    logging.info(f"- Parent ID sent to Notion API: {resolved_parent_id}")
    logging.info(f"- Workspace Name: {getattr(token_doc, 'workspace_name', 'Unknown')}")

    url = f"{NOTION_API_BASE}/pages"
    
    parent_payload = {"page_id": resolved_parent_id} if resolved_parent_type == "page" else {"database_id": resolved_parent_id}
    
    payload = {
        "parent": parent_payload,
        "properties": {
            "title": {
                "title": _build_rich_text(title)
            }
        },
        "children": _blocks_from_markdown(content)
    }
    
    import logging
    logging.info(f"NOTION DEBUG PAYLOAD: {payload}")
    print(f"NOTION DEBUG PAYLOAD: {payload}")
    
    if icon:
        payload["icon"] = {"type": "emoji", "emoji": icon} if len(icon)==1 else {"type": "external", "external": {"url": icon}}
    if cover:
        payload["cover"] = {"type": "external", "external": {"url": cover}}
    
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.post(url, headers=_get_headers(access_token), json=payload)
        
    if response.status_code != 200:
        error_detail = response.text
        try:
            error_json = response.json()
            error_detail = error_json.get("message", response.text)
        except Exception:
            pass
        raise RuntimeError(f"Notion API Create Page failed: {error_detail}")
        
    result = response.json()
    return {
        "success": True, 
        "page_id": result.get("id"),
        "page_url": result.get("url"),
        "workspace_name": "Connected Workspace", 
        "title": title
    }

async def update_page(
    page_id: str,
    title: str | None = None,
    content: str | None = None,
    organization_id: str | None = None,
    user_id: str | None = None,
    **kwargs
) -> dict:
    """Update a notion page."""
    access_token = await _get_notion_token(organization_id, user_id)
    if title:
        url = f"{NOTION_API_BASE}/pages/{page_id}"
        payload = {
            "properties": {
                "title": {
                    "title": _build_rich_text(title)
                }
            }
        }
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.patch(url, headers=_get_headers(access_token), json=payload)
            if response.status_code != 200:
                raise RuntimeError(f"Notion API Update Page failed: {response.text}")
    
    # Update page content directly appends to it
    if content:
        url = f"{NOTION_API_BASE}/blocks/{page_id}/children"
        payload = {"children": _blocks_from_markdown(content)}
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.patch(url, headers=_get_headers(access_token), json=payload)
            if response.status_code != 200:
                raise RuntimeError(f"Notion API Append (Update) failed: {response.text}")
                
    return {"success": True, "page_id": page_id}


async def append_block(
    page_id: str,
    paragraph: str | None = None,
    checklist: str | None = None,
    heading: str | None = None,
    bullets: str | None = None,
    code_block: str | None = None,
    divider: bool = False,
    quote: str | None = None,
    organization_id: str | None = None,
    user_id: str | None = None,
    **kwargs
) -> dict:
    """Append explicit blocks to an existing Notion page."""
    access_token = await _get_notion_token(organization_id, user_id)
    url = f"{NOTION_API_BASE}/blocks/{page_id}/children"
    
    children = []
    
    if heading:
        children.append({"object": "block", "type": "heading_2", "heading_2": {"rich_text": _build_rich_text(heading)}})
    if paragraph:
        children.append({"object": "block", "type": "paragraph", "paragraph": {"rich_text": _build_rich_text(paragraph)}})
    if checklist:
        for item in checklist.split('\n'):
            if item.strip():
                children.append({"object": "block", "type": "to_do", "to_do": {"rich_text": _build_rich_text(item.strip()), "checked": False}})
    if bullets:
        for item in bullets.split('\n'):
            if item.strip():
                children.append({"object": "block", "type": "bulleted_list_item", "bulleted_list_item": {"rich_text": _build_rich_text(item.strip())}})
    if code_block:
        children.append({"object": "block", "type": "code", "code": {"rich_text": _build_rich_text(code_block), "language": "plain text"}})
    if quote:
        children.append({"object": "block", "type": "quote", "quote": {"rich_text": _build_rich_text(quote)}})
    if divider:
        children.append({"object": "block", "type": "divider", "divider": {}})
        
    if not children:
        raise RuntimeError("No block content provided to append.")

    payload = {"children": children}
    
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.patch(url, headers=_get_headers(access_token), json=payload)
        
    if response.status_code != 200:
        raise RuntimeError(f"Notion API Append Blocks failed: {response.text}")
        
    result = response.json()
    return {"success": True, "appended_blocks_count": len(result.get("results", []))}

async def create_database_entry(
    database_id: str,
    properties: dict | None = None,
    status: str | None = None,
    priority: str | None = None,
    due_date: str | None = None,
    owner: str | None = None,
    name: str = "Untitled",
    organization_id: str | None = None,
    user_id: str | None = None,
    **kwargs
) -> dict:
    """Create a database item with specific properties."""
    if not database_id or not str(database_id).strip():
        if user_id:
            from syncsphere.identity.infrastructure.documents.user_document import UserDocument
            user = await UserDocument.get(user_id)
            if user and hasattr(user, "preferences") and user.preferences:
                database_id = user.preferences.default_notion_db_id

    if not database_id or not str(database_id).strip():
        raise ValueError("database_id is required and cannot be empty.")

    access_token = await _get_notion_token(organization_id, user_id)
    url = f"{NOTION_API_BASE}/pages"
    
    props = {
        "Name": {"title": _build_rich_text(name)} if not properties or "Name" not in properties else properties["Name"] 
    }
    
    if status:
        props["Status"] = {"status": {"name": status}}
    if priority:
        props["Priority"] = {"select": {"name": priority}}
    if due_date:
        props["Due Date"] = {"date": {"start": due_date}}
    if owner:
         props["Owner"] = {"rich_text": _build_rich_text(owner)} 
         
    # Merge custom properties
    if properties:
        for k, v in properties.items():
            if k not in props:
                props[k] = v
                
    payload = {
        "parent": {"database_id": database_id},
        "properties": props
    }
    
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.post(url, headers=_get_headers(access_token), json=payload)
        
    if response.status_code != 200:
        raise RuntimeError(f"Notion API Create Database Item failed: {response.text}")
        
    result = response.json()
    return {"success": True, "page_id": result.get("id"), "page_url": result.get("url")}


# Special Aliases for AI Planner Prompt Needs
async def create_meeting_notes(title: str, participants: str = "", agenda: str = "", summary: str = "", action_items: str = "", next_meeting: str = "", parent_id: str = None, organization_id: str = None, user_id: str = None, **kwargs):
    content = ""
    if participants: content += f"## Participants\n{participants}\n\n"
    if agenda: content += f"## Agenda\n{agenda}\n\n"
    if summary: content += f"## Summary\n{summary}\n\n"
    if action_items: content += f"## Action Items\n{action_items}\n\n"
    if next_meeting: content += f"## Next Meeting\n{next_meeting}\n\n"
    
    res = await create_page(title=title, content=content, parent_id=parent_id, icon="🤝", organization_id=organization_id, user_id=user_id, **kwargs)
    res["url"] = res.get("page_url") 
    return res


async def create_knowledge_base(title: str, description: str = "", steps: str = "", references: str = "", tags: str = "", parent_id: str = None, organization_id: str = None, user_id: str = None, **kwargs):
    content = ""
    if description: content += f"{description}\n\n"
    if steps: content += f"## Steps\n{steps}\n\n"
    if references: content += f"## References\n{references}\n"
    
    res = await create_page(title=title, content=content, parent_id=parent_id, icon="📚", organization_id=organization_id, user_id=user_id, **kwargs)
    res["url"] = res.get("page_url")
    return res


async def save_ai_summary(title: str, content: str, parent_id: str, organization_id: str = None, user_id: str = None, **kwargs):
    res = await create_page(title=title, content=content, parent_id=parent_id, icon="✨", organization_id=organization_id, user_id=user_id, **kwargs)
    res["url"] = res.get("page_url")
    return res
