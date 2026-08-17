import httpx
import sys
import uuid

async def main():
    async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
        # Step 1: Register
        user_email = f"test_{uuid.uuid4().hex[:6]}@example.com"
        reg_res = await client.post("/v1/auth/register", json={
            "email": user_email,
            "first_name": "Demo",
            "last_name": "User",
            "password": "Password123!",
            "org_name": "Demo Org",
            "org_slug": f"demo-org-{uuid.uuid4().hex[:6]}"
        })
        if reg_res.status_code not in (200, 201):
            print("Register failed:", reg_res.json())
            return
            
        login_res = await client.post("/v1/auth/login", json={
            "email": user_email,
            "password": "Password123!"
        })
            
        data = login_res.json().get("data", {})
        token = data.get("access_token")
        if not token:
            print("No token:", login_res.json())
            return
            
        print("Got token")
        
        # Step 2: Init Slack
        init_res = await client.post("/v1/connect/slack/init", headers={"Authorization": f"Bearer {token}"})
        print("Init Slack:", init_res.status_code, init_res.text)
        
        if init_res.status_code != 200: return
        
        auth_url = init_res.json().get("data", {}).get("auth_url") or init_res.json().get("auth_url")
        from urllib.parse import urlparse, parse_qs
        parsed = urlparse(auth_url)
        state = parse_qs(parsed.query).get("state", [None])[0]
        
        print("Parsed state from URL:", state)
        
        # Step 3: Callback
        cb_res = await client.get(f"/v1/connect/slack/callback?code=mock_code_123&state={state}", follow_redirects=False)
        print("Callback result:", cb_res.status_code, cb_res.text)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
