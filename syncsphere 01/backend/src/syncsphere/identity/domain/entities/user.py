from typing import List, Optional
from syncsphere.shared_kernel.domain.aggregate_root import AggregateRoot
from syncsphere.identity.domain.exceptions import UserDeactivatedException

class User(AggregateRoot):
    """
    User aggregate root representing a member user inside a tenant organization.
    """
    
    def __init__(
        self,
        org_id: str,
        email: str,
        password_hash: str,
        first_name: str,
        last_name: str,
        role_ids: Optional[List[str]] = None,
        status: str = "ACTIVE",
        id: Optional[str] = None,
        **kwargs
    ) -> None:
        super().__init__(id=id, **kwargs)
        self.org_id = org_id
        self.email = email.lower().strip()
        self.password_hash = password_hash
        self.first_name = first_name
        self.last_name = last_name
        self.role_ids: List[str] = role_ids or []
        self.status = status

    @property
    def full_name(self) -> str:
        """Returns concatenated full name string."""
        return f"{self.first_name} {self.last_name}"

    def check_active(self) -> None:
        """Raises UserDeactivatedException if user state is not ACTIVE."""
        if self.status != "ACTIVE":
            raise UserDeactivatedException()

    def assign_role(self, role_id: str) -> None:
        """Assigns a role to the user if not already set."""
        self.check_active()
        if role_id not in self.role_ids:
            self.role_ids.append(role_id)

    def remove_role(self, role_id: str) -> None:
        """Removes an assigned role from the user."""
        self.check_active()
        if role_id in self.role_ids:
            self.role_ids.remove(role_id)

    def deactivate(self) -> None:
        """Transition user account status to DEACTIVATED."""
        self.status = "DEACTIVATED"

    def reactivate(self) -> None:
        """Transition user account status to ACTIVE."""
        self.status = "ACTIVE"
