import logging
from datetime import datetime, timedelta
from typing import Tuple, List, Optional
from syncsphere.shared_kernel.types.result import Result
from syncsphere.shared_kernel.domain.domain_exception import ConflictException
from syncsphere.identity.domain.entities.user import User
from syncsphere.identity.domain.entities.organization import Organization
from syncsphere.identity.domain.entities.role import Role
from syncsphere.identity.domain.entities.permission import Permission
from syncsphere.identity.domain.entities.refresh_token import RefreshToken
from syncsphere.identity.domain.entities.api_key import ApiKey
from syncsphere.identity.domain.repositories import (
    UserRepository,
    OrgRepository,
    RoleRepository,
    ApiKeyRepository,
    RefreshTokenRepository,
)
from syncsphere.identity.domain.exceptions import (
    DuplicateEmailException,
    AuthenticationFailedException,
    TokenExpiredException,
    TokenInvalidException,
    RefreshTokenReusedException,
)
from syncsphere.identity.infrastructure.hashing import PasswordHasherService
from syncsphere.identity.infrastructure.jwt_service import JWTService
from syncsphere.identity.infrastructure.token_generator import TokenGeneratorService
from syncsphere.core.config.settings import settings

logger = logging.getLogger("syncsphere.identity.application.services.auth_service")

class AuthApplicationService:
    """Application Service coordinating security, logins, registrations, and key management."""

    def __init__(
        self,
        user_repo: UserRepository,
        org_repo: OrgRepository,
        role_repo: RoleRepository,
        api_key_repo: ApiKeyRepository,
        token_repo: RefreshTokenRepository,
        hasher: PasswordHasherService,
        jwt_service: JWTService,
        token_gen: TokenGeneratorService,
    ) -> None:
        self.user_repo = user_repo
        self.org_repo = org_repo
        self.role_repo = role_repo
        self.api_key_repo = api_key_repo
        self.token_repo = token_repo
        self.hasher = hasher
        self.jwt_service = jwt_service
        self.token_gen = token_gen

    async def register_user(
        self,
        email: str,
        password: str,
        first_name: str,
        last_name: str,
        org_name: str,
        org_slug: str
    ) -> Result[str, Exception]:
        """Registers a new organization and default administrator user."""
        logger.info("Processing registration for email: %s, org: %s", email, org_slug)
        
        # 1. Validate email duplicate
        existing_user = await self.user_repo.get_by_email(email)
        if existing_user:
            return Result.fail(DuplicateEmailException(email))

        # 2. Validate slug duplicate
        existing_org = await self.org_repo.get_by_slug(org_slug)
        if existing_org:
            return Result.fail(ConflictException(
                code="DUPLICATE_SLUG",
                message=f"Organization slug '{org_slug}' is already taken."
            ))

        # 3. Create Org Entity
        org = Organization(name=org_name, slug=org_slug)
        await self.org_repo.save(org)

        # 4. Create default ADMIN Role
        admin_permission = Permission(resource_type="*", resource_id="*", actions=["*"])
        admin_role = Role(
            org_id=org.id,
            name="ADMIN",
            description="Default Administrator Role with all permissions",
            is_system_role=True,
            permissions=[admin_permission]
        )
        await self.role_repo.save(admin_role)

        # 5. Hash Password & Create User
        password_hash = self.hasher.hash_password(password)
        user = User(
            org_id=org.id,
            email=email,
            password_hash=password_hash,
            first_name=first_name,
            last_name=last_name,
            role_ids=[admin_role.id]
        )
        await self.user_repo.save(user)

        logger.info("Registration successful for user_id: %s in org_id: %s", user.id, org.id)
        return Result.ok(user.id)

    async def login(
        self,
        email: str,
        password: str,
        device_info: Optional[dict] = None
    ) -> Result[Tuple[str, str], Exception]:
        """Authenticates user and returns fresh access/refresh token pair."""
        user = await self.user_repo.get_by_email(email)
        if not user:
            return Result.fail(AuthenticationFailedException())

        # Validate account status
        try:
            user.check_active()
        except Exception as e:
            return Result.fail(e)

        # Verify password hash
        if not self.hasher.verify_password(user.password_hash, password):
            return Result.fail(AuthenticationFailedException())

        # Resolve role names
        roles_names = []
        for role_id in user.role_ids:
            role = await self.role_repo.get_by_id(role_id)
            if role:
                roles_names.append(role.name)

        # Generate JWT access token
        access_token = self.jwt_service.create_access_token(
            user_id=user.id,
            org_id=user.org_id,
            roles=roles_names
        )

        # Generate refresh token
        raw_refresh, token_hash = self.token_gen.generate_refresh_token()
        expires_at = datetime.utcnow() + timedelta(seconds=settings.jwt_refresh_token_ttl)
        
        refresh_token_entity = RefreshToken(
            org_id=user.org_id,
            user_id=user.id,
            token_hash=token_hash,
            expires_at=expires_at,
            device_info=device_info
        )
        await self.token_repo.save(refresh_token_entity)

        return Result.ok((access_token, raw_refresh))

    async def refresh_access_token(
        self,
        raw_refresh_token: str,
        device_info: Optional[dict] = None
    ) -> Result[Tuple[str, str], Exception]:
        """Validates refresh token and executes single-use token rotation."""
        token_hash = self.token_gen.hash_token(raw_refresh_token)
        stored_token = await self.token_repo.get_by_hash(token_hash)
        
        if not stored_token:
            return Result.fail(TokenInvalidException("Refresh token is unrecognized/invalid."))

        # Replay Attack Detection: If token is revoked, invalidate entire user session chain!
        if stored_token.is_revoked:
            logger.warning("Replay attack detected! Revoking all refresh tokens for user: %s", stored_token.user_id)
            await self.token_repo.revoke_all_for_user(stored_token.user_id)
            return Result.fail(RefreshTokenReusedException())

        if stored_token.is_expired:
            return Result.fail(TokenExpiredException("Refresh token has expired."))

        # Get User details
        user = await self.user_repo.get_by_id(stored_token.user_id)
        if not user or user.status != "ACTIVE":
            return Result.fail(AuthenticationFailedException("User account is inactive."))

        # Resolve Roles
        roles_names = []
        for role_id in user.role_ids:
            role = await self.role_repo.get_by_id(role_id)
            if role:
                roles_names.append(role.name)

        # Generate new Access Token
        new_access = self.jwt_service.create_access_token(
            user_id=user.id,
            org_id=user.org_id,
            roles=roles_names
        )

        # Generate Rotated Refresh Token
        new_raw_refresh, new_token_hash = self.token_gen.generate_refresh_token()
        new_expires_at = datetime.utcnow() + timedelta(seconds=settings.jwt_refresh_token_ttl)
        
        new_refresh_entity = RefreshToken(
            org_id=user.org_id,
            user_id=user.id,
            token_hash=new_token_hash,
            expires_at=new_expires_at,
            device_info=device_info
        )
        await self.token_repo.save(new_refresh_entity)

        # Invalidate old token and set replaced_by link
        stored_token.revoke(replaced_by=new_refresh_entity.id)
        await self.token_repo.save(stored_token)

        return Result.ok((new_access, new_raw_refresh))

    async def logout(self, raw_refresh_token: str) -> Result[bool, Exception]:
        """Revokes the refresh token to terminate session access."""
        token_hash = self.token_gen.hash_token(raw_refresh_token)
        stored_token = await self.token_repo.get_by_hash(token_hash)
        
        if stored_token:
            stored_token.revoke()
            await self.token_repo.save(stored_token)
            return Result.ok(True)
        return Result.ok(False)

    async def rotate_api_key(
        self,
        org_id: str,
        user_id: str,
        name: str,
        scopes: List[str],
        expires_in_days: Optional[int] = None
    ) -> Result[Tuple[str, ApiKey], Exception]:
        """Creates a scoped API Key. Returns (raw_key, ApiKey entity)."""
        raw_key, prefix, key_hash = self.token_gen.generate_api_key()
        
        expires_at = None
        if expires_in_days:
            expires_at = datetime.utcnow() + timedelta(days=expires_in_days)

        api_key = ApiKey(
            org_id=org_id,
            user_id=user_id,
            name=name,
            key_hash=key_hash,
            key_prefix=prefix,
            scopes=scopes,
            expires_at=expires_at
        )
        await self.api_key_repo.save(api_key)
        
        return Result.ok((raw_key, api_key))
