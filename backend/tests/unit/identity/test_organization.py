from syncsphere.identity.domain.entities.organization import Organization

def test_organization_creation():
    """Tests that an Organization aggregate is initialized with correct settings and quotas."""
    org = Organization(name="Acme Corp", slug="acme-corp")
    assert org.name == "Acme Corp"
    assert org.slug == "acme-corp"
    assert org.billing_tier == "FREE"
    assert org.quotas["max_users"] == 5
    assert org.feature_flags["reflection_enabled"] is False

def test_organization_upgrade_tier():
    """Tests upgrading billing tier and updating quotas."""
    org = Organization(name="Acme Corp", slug="acme-corp")
    new_limits = {
        "max_workflows": 100,
        "max_executions_per_day": 10000,
        "max_connectors": 50,
        "max_users": 200
    }
    org.upgrade_tier("PROFESSIONAL", new_limits)
    assert org.billing_tier == "PROFESSIONAL"
    assert org.quotas["max_users"] == 200
    assert org.quotas["max_workflows"] == 100

def test_organization_toggle_feature_flag():
    """Tests enabling/disabling feature flags."""
    org = Organization(name="Acme Corp", slug="acme-corp")
    org.toggle_feature_flag("reflection_enabled", True)
    assert org.feature_flags["reflection_enabled"] is True
