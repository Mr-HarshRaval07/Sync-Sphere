from typing import Optional
from syncsphere.shared_kernel.types.contracts import BaseQuery

class ValidatePermissionQuery(BaseQuery):
    """Query to check if a user has permissions for a specific action."""
    user_id: str
    resource_type: str
    resource_id: str
    action: str


class GetUserProfileQuery(BaseQuery):
    """Query to retrieve user profile data."""
    user_id: str


class ListUsersQuery(BaseQuery):
    """Query to list users within an organization."""
    org_id: str
    page: int = 1
    page_size: int = 20


class GetOrgDetailsQuery(BaseQuery):
    """Query to retrieve organization details."""
    org_id: str


class ListRolesQuery(BaseQuery):
    """Query to list all roles configured for an organization."""
    org_id: str
