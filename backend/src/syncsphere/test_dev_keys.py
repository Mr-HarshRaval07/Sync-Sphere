import asyncio
import os
import sys

os.environ["HTTP_PORT"] = "8000"
os.environ["MONGODB_URI"] = "mongodb://localhost:27017"
os.environ["JWKS_URL"] = "http://localhost:8000/.well-known/jwks.json"
os.environ["JWT_AUDIENCE"] = "syncsphere"
os.environ["JWT_ISSUER"] = "syncsphere"

from fastapi.testclient import TestClient
from syncsphere.main import app
from syncsphere.shared_kernel.infrastructure.http.dependencies import get_org_id, verify_jwt

# Disable JWT error and force test mode
app.dependency_overrides[get_org_id] = lambda: "org_test"

def run_test():
    print("Starting API Developer Keys Test...")
    with TestClient(app) as client:
        # Create a key
        headers = {"Authorization": "Bearer test"}
        resp = client.post("/v1/developer-keys", json={"name": "My Script Key"}, headers=headers)
        if resp.status_code != 201:
            print("Failed to create key:", resp.status_code, resp.text)
            sys.exit(1)
        
        data = resp.json()
        raw_key = data["key"]
        key_id = data["id"]
        print(f"Created Key: {raw_key} with ID {key_id}")
        
        # List keys using 'test' user
        resp = client.get("/v1/developer-keys", headers=headers)
        keys = resp.json()
        print(f"Found {len(keys)} keys for the user. First: {keys[0]['name']} - {keys[0]['status']}")
        if len(keys) == 0:
            print("Failed to list keys!")
            sys.exit(1)
        
        # Test Authenticating with the newly generated API Key!
        api_key_headers = {"Authorization": f"Bearer {raw_key}"}
        # Try to call GET /v1/developer-keys using the API key itself as auth
        api_resp = client.get("/v1/developer-keys", headers=api_key_headers)
        if api_resp.status_code == 200:
            print("Successfully authenticated using the developer API key!")
        else:
            print("Failed to authenticate with developer API key:", api_resp.status_code, api_resp.text)
            sys.exit(1)
            
        # Revoke Key
        print(f"Revoking key {key_id}")
        del_resp = client.delete(f"/v1/developer-keys/{key_id}", headers=headers)
        if del_resp.status_code != 204:
            print("Failed to revoke key:", del_resp.status_code, del_resp.text)
            sys.exit(1)
            
        print("Key revoked successfully.")
        
        # Test Authenticating with the revoked API key
        api_resp_revoked = client.get("/v1/developer-keys", headers=api_key_headers)
        if api_resp_revoked.status_code == 401:
            print("Successfully rejected the revoked developer API key with 401!")
        else:
            print("Danger: Auth allowed a revoked developer API key!", api_resp_revoked.status_code)
            sys.exit(1)
            
        print("All Tests Passed!")

if __name__ == "__main__":
    run_test()
