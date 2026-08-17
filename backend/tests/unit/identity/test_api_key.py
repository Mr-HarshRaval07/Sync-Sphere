from datetime import datetime, timedelta
from syncsphere.identity.domain.entities.api_key import ApiKey

def test_api_key_creation():
    """Tests that an ApiKey entity is initialized correctly."""
    api_key = ApiKey(
        org_id="org_123",
        user_id="user_123",
        name="CI/CD Key",
        key_hash="sha256_hash",
        key_prefix="sk_live_abcdef",
        scopes=["workflows:read"]
    )
    assert api_key.org_id == "org_123"
    assert api_key.user_id == "user_123"
    assert api_key.name == "CI/CD Key"
    assert api_key.scopes == ["workflows:read"]
    assert api_key.status == "ACTIVE"
    assert api_key.is_expired is False
    assert api_key.is_active is True

def test_api_key_expiry():
    """Tests that ApiKey correctly computes expiration logic."""
    past_date = datetime.utcnow() - timedelta(days=1)
    api_key = ApiKey(
        org_id="org_123",
        user_id="user_123",
        name="Expired Key",
        key_hash="sha256_hash",
        key_prefix="sk_live_abcdef",
        scopes=["workflows:read"],
        expires_at=past_date
    )
    assert api_key.is_expired is True
    assert api_key.is_active is False

def test_api_key_revocation():
    """Tests that revoking an ApiKey transitions state correctly."""
    api_key = ApiKey(
        org_id="org_123",
        user_id="user_123",
        name="Active Key",
        key_hash="sha256_hash",
        key_prefix="sk_live_abcdef",
        scopes=["workflows:read"]
    )
    api_key.revoke()
    assert api_key.status == "REVOKED"
    assert api_key.is_active is False
