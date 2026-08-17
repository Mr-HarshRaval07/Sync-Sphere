import asyncio, json
import httpx
from syncsphere.connectors.presentation.slack_actions import send_slack_message

async def run_test():
    try:
        # We need an organization_id that has a token. Let's just mock _get_slack_token.
        import syncsphere.connectors.presentation.slack_actions as sa
        sa._get_slack_token = lambda org_id: asyncio.sleep(0, result="mock_token")
        
        # We also need to mock httpx post
        original_post = httpx.AsyncClient.post
        
        async def mock_post(*args, **kwargs):
            class MockResponse:
                def json(self): return {"ok": False, "error": "account_inactive"}
            return MockResponse()
            
        httpx.AsyncClient.post = mock_post
        
        try:
            await send_slack_message(message="Hello", channel="#general", organization_id="test_org")
        except Exception as e:
            print("Captured Error:", type(e).__name__, str(e))
            
    finally:
        pass

if __name__ == "__main__":
    asyncio.run(run_test())
