import asyncio
from fastapi.testclient import TestClient
from syncsphere.main import app

def test_jwt_lifecycle():
    print("[1] Registering/Logging In...")
    test_email = "test.jwt2@syncsphere.ai"
    
    with TestClient(app) as client:
        login_res = client.post("/v1/auth/login", json={
            "email": test_email, "password": "Password123!"
        })
        
        if login_res.status_code == 401:
            reg_res = client.post("/v1/auth/register", json={
                "email": test_email,
                "password": "Password123!",
                "first_name": "Test",
                "last_name": "JWT",
                "org_name": "JWT Corp",
                "org_slug": "jwt-corp-2"
            })
            login_res = client.post("/v1/auth/login", json={
                "email": test_email, "password": "Password123!"
            })
        
        login_data = login_res.json()
        print(f"Login Response: {login_res.status_code}")
        
        access_token = login_data["data"]["access_token"]
        headers = {"Authorization": f"Bearer {access_token}"}
        
        tasks_res = client.get("/v1/tasks", headers=headers)
        print(f"Valid GET /v1/tasks Status: {tasks_res.status_code}")
        
        invalid_headers = {"Authorization": f"Bearer {access_token[:-5]}abcde"}
        expired_res = client.get("/v1/tasks", headers=invalid_headers)
        print(f"Expired/Invalid GET /v1/tasks Status: {expired_res.status_code}")
        
        print("[2] Refreshing session...")
        refresh_res = client.post("/v1/auth/refresh", json={})
        print(f"Refresh Response Status: {refresh_res.status_code}")
        
        if refresh_res.status_code == 200:
            new_access_token = refresh_res.json()["data"]["access_token"]
            new_headers = {"Authorization": f"Bearer {new_access_token}"}
            
            refreshed_tasks_res = client.get("/v1/tasks", headers=new_headers)
            print(f"Post-Refresh GET /v1/tasks Status: {refreshed_tasks_res.status_code}")
        else:
            print(f"Refresh failed: {refresh_res.text}")

if __name__ == "__main__":
    test_jwt_lifecycle()
