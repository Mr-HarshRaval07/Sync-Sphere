import pytest
from fastapi.testclient import TestClient
from syncsphere.main import app

client = TestClient(app)

def test_auth_registration_and_login_flow():
    """Tests the full user journey: register, login, authenticated request, and token refresh."""
    
    # 1. Register organization and user
    register_payload = {
        "email": "admin@acme.ai",
        "password": "supersecretpassword123!",
        "first_name": "Alice",
        "last_name": "Smith",
        "org_name": "Acme Corp",
        "org_slug": "acme-corp"
    }
    resp = client.post("/v1/auth/register", json=register_payload)
    assert resp.status_code == 201
    reg_data = resp.json()
    assert "user_id" in reg_data["data"]
    assert reg_data["data"]["status"] == "registered"

    # Try duplicate registration
    resp_dup = client.post("/v1/auth/register", json=register_payload)
    assert resp_dup.status_code == 409
    assert resp_dup.json()["error"]["code"] == "DUPLICATE_EMAIL"

    # 2. Login user
    login_payload = {
        "email": "admin@acme.ai",
        "password": "supersecretpassword123!"
    }
    resp_login = client.post("/v1/auth/login", json=login_payload)
    assert resp_login.status_code == 200
    login_data = resp_login.json()["data"]
    access_token = login_data["access_token"]
    refresh_token = login_data["refresh_token"]
    assert access_token is not None
    assert refresh_token is not None

    # 3. Call authenticated /users/me
    headers = {"Authorization": f"Bearer {access_token}"}
    resp_me = client.get("/v1/users/me", headers=headers)
    assert resp_me.status_code == 200
    me_data = resp_me.json()["data"]
    assert me_data["email"] == "admin@acme.ai"
    assert me_data["first_name"] == "Alice"
    assert me_data["status"] == "ACTIVE"

    # 4. Attempt unauthenticated call
    client.cookies.clear()
    resp_me_unauth = client.get("/v1/users/me")
    assert resp_me_unauth.status_code == 401

    # 5. Refresh token rotation
    refresh_payload = {
        "refresh_token": refresh_token
    }
    resp_refresh = client.post("/v1/auth/refresh", json=refresh_payload)
    assert resp_refresh.status_code == 200
    refresh_data = resp_refresh.json()["data"]
    new_access = refresh_data["access_token"]
    new_refresh = refresh_data["refresh_token"]
    assert new_access is not None
    assert new_refresh != refresh_token

    # 6. Verify rotated token works
    new_headers = {"Authorization": f"Bearer {new_access}"}
    resp_me_rotated = client.get("/v1/users/me", headers=new_headers)
    assert resp_me_rotated.status_code == 200

    # 7. Replay attack verification: Old refresh token should be rejected (revoked on replay)
    resp_replay = client.post("/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert resp_replay.status_code == 401
    assert resp_replay.json()["error"]["code"] == "AUTH_REFRESH_TOKEN_REUSED"

def test_rbac_endpoint_protections():
    """Tests role-based access controls (RBAC) on custom role generation."""
    
    # Register an admin user and a regular user in Acme Corp
    admin_payload = {
        "email": "admin2@acme.ai",
        "password": "supersecretpassword123!",
        "first_name": "Bob",
        "last_name": "Jones",
        "org_name": "Acme Corp 2",
        "org_slug": "acme-corp-2"
    }
    client.post("/v1/auth/register", json=admin_payload)
    
    # Login as admin to get token and org_id
    resp_admin_login = client.post("/v1/auth/login", json={"email": "admin2@acme.ai", "password": "supersecretpassword123!"})
    admin_claims = resp_admin_login.json()["data"]
    admin_token = admin_claims["access_token"]
    
    # Register a regular user (via invitation mock)
    # Get user profile to check org
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    resp_me = client.get("/v1/users/me", headers=admin_headers)
    org_id = resp_me.json()["data"]["org_id"]
    
    # Create a regular role
    role_payload = {
        "name": "DEVELOPER",
        "description": "Developer role",
        "permissions": [
            {
                "resource_type": "WORKFLOW",
                "resource_id": "*",
                "actions": ["read", "write"]
            }
        ]
    }
    resp_role = client.post("/v1/roles", json=role_payload, headers=admin_headers)
    assert resp_role.status_code == 201
    dev_role_id = resp_role.json()["data"]["id"]
    
    # Create the regular user (invite)
    invite_payload = {
        "email": "dev@acme.ai",
        "first_name": "Dev",
        "last_name": "Tester",
        "role_ids": [dev_role_id]
    }
    resp_invite = client.post("/v1/users", json=invite_payload, headers=admin_headers)
    assert resp_invite.status_code == 201
    dev_user_id = resp_invite.json()["data"]["id"]
    
    # Login as regular user (dummy pass set during invite)
    resp_dev_login = client.post("/v1/auth/login", json={"email": "dev@acme.ai", "password": "temporary_invite_pass_123!"})
    dev_token = resp_dev_login.json()["data"]["access_token"]
    dev_headers = {"Authorization": f"Bearer {dev_token}"}
    
    # 1. Regular user lists roles (allowed)
    resp_list_roles = client.get("/v1/roles", headers=dev_headers)
    assert resp_list_roles.status_code == 200
    
    # 2. Regular user tries to create a role (forbidden)
    resp_create_fail = client.post("/v1/roles", json=role_payload, headers=dev_headers)
    assert resp_create_fail.status_code == 403
    assert resp_create_fail.json()["error"]["code"] == "INSUFFICIENT_PERMISSIONS"
