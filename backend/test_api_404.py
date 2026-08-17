import httpx
import asyncio

async def test_api():
    # Attempt to POST using a mock JWT since we know the JWT secret
    import jwt
    import time
    
    secret = "supersecretjwtkeythatisthirtytwobyteslongtobesecure"
    token = jwt.encode(
        {"sub": "test_user_from_script", "org": "6a52824dbd1002d93a5495ae", "exp": time.time() + 3600}, 
        secret, 
        algorithm="HS256"
    )
    
    url = "http://localhost:8000/v1/approvals/unknown/approve"
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        print(f"POSTing to {url}")
        res = await client.post(
            url, 
            json={"comment": "test"}, 
            headers={"Authorization": f"Bearer {token}"}
        )
        print(f"Status: {res.status_code}")
        print(f"Body: {res.text}")

asyncio.run(test_api())
