import logging
from typing import List, Optional
from syncsphere.shared_kernel.types.result import Result
from syncsphere.shared_kernel.domain.domain_exception import EntityNotFoundException
from syncsphere.identity.domain.entities.role import Role
from syncsphere.identity.domain.entities.permission import Permission
from syncsphere.identity.domain.repositories import UserRepository, RoleRepository
from syncsphere.identity.domain.exceptions import DuplicateRoleException

logger = logging.getLogger("syncsphere.identity.application.services.rbac_service")

class RBACApplicationService:
    """Application Service coordinating RBAC, user permissions validation, and role assignments."""

    def __init__(
        self,
        user_repo: UserRepository,
        role_repo: RoleRepository
    ) -> None:
        self.user_repo = user_repo
        self.role_repo = role_repo

    async def validate_permission(
        self,
        user_id: str,
        resource_type: str,
        resource_id: str,
        action: str
    ) -> bool:
        """Evaluates whether the specified user has authorization for a given action."""
        user = await self.user_repo.get_by_id(user_id)
        if not user or user.status != "ACTIVE":
            return False

        # Loop through all assigned roles
        for role_id in user.role_ids:
            role = await self.role_repo.get_by_id(role_id)
            if not role:
                continue
            
            # Check permissions inside the role
            if role.has_permission(resource_type, resource_id, action):
                return True
                
        return False

    async def create_role(
        self,
        org_id: str,
        name: str,
        description: Optional[str] = None,
        permissions: Optional[List[Permission]] = None
    ) -> Result[Role, Exception]:
        """Creates a custom security role for the tenant."""
        existing_role = await self.role_repo.get_by_name(org_id, name)
        if existing_role:
            return Result.fail(DuplicateRoleException(name))

        role = Role(
            org_id=org_id,
            name=name,
            description=description,
            is_system_role=False,
            permissions=permissions
        )
        await self.role_repo.save(role)
        return Result.ok(role)

    async def assign_role_to_user(self, user_id: str, role_id: str) -> Result[bool, Exception]:
        """Maps a role assignment to a user."""
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            return Result.fail(EntityNotFoundException("USER_NOT_FOUND", "User not found."))

        role = await self.role_repo.get_by_id(role_id)
        if not role:
            return Result.fail(EntityNotFoundException("ROLE_NOT_FOUND", "Role not found."))

        try:
            user.assign_role(role_id)
            await self.user_repo.save(user)
            return Result.ok(True)
        except Exception as e:
            return Result.fail(e)

    async def remove_role_from_user(self, user_id: str, role_id: str) -> Result[bool, Exception]:
        """Removes a role assignment from a user."""
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            return Result.fail(EntityNotFoundException("USER_NOT_FOUND", "User not found."))

        try:
            user.remove_role(role_id)
            await self.user_repo.save(user)
            return Result.ok(True)
        except Exception as e:
            return Result.fail(e)
