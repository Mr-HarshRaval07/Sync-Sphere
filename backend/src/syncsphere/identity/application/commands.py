from pydantic import EmailStr, Field
from typing import List, Optional
from syncsphere.shared_kernel.types.contracts import BaseCommand

class RegisterUserCommand(BaseCommand):
    """Command to register a new tenant organization and its admin user."""
    email: EmailStr
    password: str = Field(..., min_length=8)
    first_name: str = Field(..., min_length=1)
    last_name: str = Field(..., min_length=1)
    org_name: str = Field(..., min_length=2)
    org_slug: str = Field(..., min_length=2)


class LoginCommand(BaseCommand):
    """Command to authenticate email/password credentials."""
    email: EmailStr
    password: str


class RefreshAccessTokenCommand(BaseCommand):
    """Command to exchange a refresh token for rotated tokens."""
    refresh_token: str
    device_info: Optional[dict] = None


class CreateOrganizationCommand(BaseCommand):
    """Command to create a new organization tenant."""
    name: str
    slug: str


class InviteMemberCommand(BaseCommand):
    """Command to invite a new user member to an organization."""
    email: EmailStr
    first_name: str
    last_name: str
    role_ids: List[str]


class AssignRoleCommand(BaseCommand):
    """Command to assign a role to a user."""
    user_id: str
    role_id: str


class RemoveRoleCommand(BaseCommand):
    """Command to remove a role from a user."""
    user_id: str
    role_id: str


class DeactivateUserCommand(BaseCommand):
    """Command to deactivate a user."""
    user_id: str


class RotateApiKeyCommand(BaseCommand):
    """Command to generate/rotate API key credentials."""
    user_id: str
    name: str
    scopes: List[str]
    expires_in_days: Optional[int] = None
