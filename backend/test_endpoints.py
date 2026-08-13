import sys
import os
import asyncio
import httpx
from httpx import AsyncClient, ASGITransport

app_dir = os.path.dirname(__file__)
sys.path.append(os.path.join(app_dir, 'src'))

from syncsphere.main import app

async def test_routes():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        print("--- Testing /v1/tasks ---")
        from syncsphere.shared_kernel.infrastructure.http.dependencies import verify_jwt
        app.dependency_overrides[verify_jwt] = lambda: {"org": "org-default", "sub": "user-123"}
        
        res1 = await ac.get("/v1/tasks")
        print(f"GET /v1/tasks -> {res1.status_code}")
        
        res2 = await ac.get("/v1/tasks/invalid-id")
        print(f"GET /v1/tasks/invalid-id -> {res2.status_code} {res2.text}")
        
        res3 = await ac.get("/v1/connect/status")
        print(f"GET /v1/connect/status -> {res3.status_code} {res3.text}")
        
        res4 = await ac.get("/v1/connectors/status")
        print(f"GET /v1/connectors/status -> {res4.status_code} {res4.text}")
        
        print("--- Done ---")
        
if __name__ == "__main__":
    asyncio.run(test_routes())
