import pytest
from syncsphere.identity.domain.entities.user import User
from syncsphere.identity.domain.exceptions import UserDeactivatedException

def test_user_creation():
    """Tests that a User aggregate root is initialized with correct fields."""
    user = User(
        org_id="org_123",
        email="test@syncsphere.ai",
        password_hash="argon2_hashed_pass",
        first_name="John",
        last_name="Doe"
    )
    assert user.org_id == "org_123"
    assert user.email == "test@syncsphere.ai"
    assert user.password_hash == "argon2_hashed_pass"
    assert user.first_name == "John"
    assert user.last_name == "Doe"
    assert user.status == "ACTIVE"
    assert user.role_ids == []
    assert user.full_name == "John Doe"

def test_user_deactivate_reactivate():
    """Tests that user deactivation and reactivation updates state correctly."""
    user = User(
        org_id="org_123",
        email="test@syncsphere.ai",
        password_hash="argon2_hashed_pass",
        first_name="John",
        last_name="Doe"
    )
    user.check_active()  # Should not raise exception
    
    user.deactivate()
    assert user.status == "DEACTIVATED"
    with pytest.raises(UserDeactivatedException):
        user.check_active()
        
    user.reactivate()
    assert user.status == "ACTIVE"
    user.check_active()  # Should not raise exception

def test_user_role_assignment():
    """Tests assigning and removing roles for a User entity."""
    user = User(
        org_id="org_123",
        email="test@syncsphere.ai",
        password_hash="argon2_hashed_pass",
        first_name="John",
        last_name="Doe"
    )
    role_id = "role_admin_123"
    
    user.assign_role(role_id)
    assert role_id in user.role_ids
    assert len(user.role_ids) == 1
    
    # Try duplicating role assignment
    user.assign_role(role_id)
    assert len(user.role_ids) == 1
    
    # Remove role
    user.remove_role(role_id)
    assert role_id not in user.role_ids
    assert len(user.role_ids) == 0
