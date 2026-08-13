from typing import Optional, Dict, Any
from syncsphere.shared_kernel.domain.aggregate_root import AggregateRoot

class Organization(AggregateRoot):
    """
    Organization aggregate root representing the core tenant boundary.
    All data operations scope to this partition.
    """
    
    def __init__(
        self,
        name: str,
        slug: str,
        billing_tier: str = "FREE",
        quotas: Optional[Dict[str, int]] = None,
        settings: Optional[Dict[str, Any]] = None,
        feature_flags: Optional[Dict[str, bool]] = None,
        id: Optional[str] = None,
        **kwargs
    ) -> None:
        super().__init__(id=id, **kwargs)
        self.name = name
        self.slug = slug
        self.billing_tier = billing_tier
        
        # Initialize default limits based on Free tier if not provided
        self.quotas = quotas or {
            "max_workflows": 10,
            "max_executions_per_day": 100,
            "max_connectors": 5,
            "max_users": 5
        }
        self.settings = settings or {}
        self.feature_flags = feature_flags or {
            "reflection_enabled": False,
            "approval_enabled": True
        }

    def upgrade_tier(self, new_tier: str, new_limits: Dict[str, int]) -> None:
        """Upgrades billing tier and resets quota limits."""
        self.billing_tier = new_tier
        self.quotas.update(new_limits)
        
    def toggle_feature_flag(self, flag: str, enabled: bool) -> None:
        """Configures feature flag enablement."""
        self.feature_flags[flag] = enabled
