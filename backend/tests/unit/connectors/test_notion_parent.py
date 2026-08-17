import pytest
from unittest.mock import patch, MagicMock, AsyncMock

import syncsphere.connectors.presentation.notion_actions as notion_actions

@pytest.mark.asyncio
async def test_notion_parent_payload_page():
    """Test A: Parent = Page, Expected: parent.page_id"""
    with patch("syncsphere.connectors.presentation.notion_actions._get_notion_doc", new_callable=AsyncMock) as mock_get_doc, \
         patch("syncsphere.connectors.presentation.notion_actions.httpx.AsyncClient") as mock_client:
         
        mock_doc = MagicMock()
        mock_doc.access_token = "fake_token"
        mock_doc.accessible_pages = []
        mock_get_doc.return_value = mock_doc
        
        # We need mock_client.post to return a valid response (200)
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": "new_page_id", "url": "https://notion.so/test"}
        
        mock_post = AsyncMock(return_value=mock_response)
        
        # Async context manager mock
        mock_client.return_value.__aenter__.return_value.post = mock_post
        
        # Execute
        await notion_actions.create_page(
            title="Test Page",
            parent_id="abc-123",
            parent_type="page",
            organization_id="org1",
            user_id="user1"
        )
        
        # Verify
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        
        payload = kwargs.get("json")
        assert "parent" in payload
        assert "page_id" in payload["parent"]
        assert payload["parent"]["page_id"] == "abc-123"
        assert "database_id" not in payload["parent"]

@pytest.mark.asyncio
async def test_notion_parent_payload_database():
    """Test B: Parent = Database, Expected: parent.database_id"""
    with patch("syncsphere.connectors.presentation.notion_actions._get_notion_doc", new_callable=AsyncMock) as mock_get_doc, \
         patch("syncsphere.connectors.presentation.notion_actions.httpx.AsyncClient") as mock_client:
         
        mock_doc = MagicMock()
        mock_doc.access_token = "fake_token"
        mock_doc.accessible_pages = []
        mock_get_doc.return_value = mock_doc
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": "new_page_id", "url": "https://notion.so/test"}
        
        mock_post = AsyncMock(return_value=mock_response)
        mock_client.return_value.__aenter__.return_value.post = mock_post
        
        # Execute
        await notion_actions.create_page(
            title="Test Page",
            parent_id="def-456",
            parent_type="database",
            organization_id="org1",
            user_id="user1"
        )
        
        # Verify
        payload = mock_post.call_args.kwargs.get("json")
        assert "parent" in payload
        assert "database_id" in payload["parent"]
        assert payload["parent"]["database_id"] == "def-456"
        assert "page_id" not in payload["parent"]
