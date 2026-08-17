from syncsphere.identity.domain.entities.organization import Organization
from syncsphere.identity.domain.entities.role import Role
from syncsphere.identity.domain.entities.permission import Permission
from syncsphere.identity.domain.entities.user import User
from syncsphere.identity.domain.entities.api_key import ApiKey
from syncsphere.identity.domain.entities.refresh_token import RefreshToken

from syncsphere.identity.infrastructure.documents.org_document import OrgDocument
from syncsphere.identity.infrastructure.documents.role_document import RoleDocument, PermissionEmbed
from syncsphere.identity.infrastructure.documents.user_document import UserDocument
from syncsphere.identity.infrastructure.documents.api_key_document import ApiKeyDocument
from syncsphere.identity.infrastructure.documents.refresh_token_document import RefreshTokenDocument

class IdentityMappers:
    """Utility class providing mapping conversions between Domain models and Beanie Documents."""

    # ==========================================================================
    # Organization mappings
    # ==========================================================================
    @staticmethod
    def org_to_domain(doc: OrgDocument) -> Organization:
        return Organization(
            name=doc.name,
            slug=doc.slug,
            billing_tier=doc.billing_tier,
            quotas=doc.quotas,
            settings=doc.settings,
            feature_flags=doc.feature_flags,
            id=str(doc.id),
            created_at=doc.created_at,
            updated_at=doc.updated_at
        )

    @staticmethod
    def org_to_document(domain: Organization) -> OrgDocument:
        doc = OrgDocument(
            name=domain.name,
            slug=domain.slug,
            billing_tier=domain.billing_tier,
            quotas=domain.quotas,
            settings=domain.settings,
            feature_flags=domain.feature_flags,
            created_at=domain.created_at,
            updated_at=domain.updated_at
        )
        if domain.id:
            # Map string UUID/ObjectId back if preset
            # In Beanie, id can be overridden or mapped on initialization
            # We map custom IDs using Beanie document initialization helpers
            pass
        return doc

    # ==========================================================================
    # Role mappings
    # ==========================================================================
    @staticmethod
    def role_to_domain(doc: RoleDocument) -> Role:
        permissions = [
            Permission(
                resource_type=p.resource_type,
                resource_id=p.resource_id,
                actions=p.actions
            ) for p in doc.permissions
        ]
        return Role(
            org_id=doc.org_id,
            name=doc.name,
            description=doc.description,
            is_system_role=doc.is_system_role,
            permissions=permissions,
            id=str(doc.id),
            created_at=doc.created_at,
            updated_at=doc.updated_at
        )

    @staticmethod
    def role_to_document(domain: Role) -> RoleDocument:
        permissions = [
            PermissionEmbed(
                resource_type=p.resource_type,
                resource_id=p.resource_id,
                actions=p.actions
            ) for p in domain.permissions
        ]
        return RoleDocument(
            org_id=domain.org_id,
            name=domain.name,
            description=domain.description,
            is_system_role=domain.is_system_role,
            permissions=permissions,
            created_at=domain.created_at,
            updated_at=domain.updated_at
        )

    # ==========================================================================
    # User mappings
    # ==========================================================================
    @staticmethod
    def user_to_domain(doc: UserDocument) -> User:
        return User(
            org_id=doc.org_id,
            email=doc.email,
            password_hash=doc.password_hash,
            first_name=doc.first_name,
            last_name=doc.last_name,
            role_ids=doc.role_ids,
            status=doc.status,
            id=str(doc.id),
            created_at=doc.created_at,
            updated_at=doc.updated_at
        )

    @staticmethod
    def user_to_document(domain: User) -> UserDocument:
        return UserDocument(
            org_id=domain.org_id,
            email=domain.email,
            password_hash=domain.password_hash,
            first_name=domain.first_name,
            last_name=domain.last_name,
            role_ids=domain.role_ids,
            status=domain.status,
            created_at=domain.created_at,
            updated_at=domain.updated_at
        )

    # ==========================================================================
    # ApiKey mappings
    # ==========================================================================
    @staticmethod
    def api_key_to_domain(doc: ApiKeyDocument) -> ApiKey:
        return ApiKey(
            org_id=doc.org_id,
            user_id=doc.user_id,
            name=doc.name,
            key_hash=doc.key_hash,
            key_prefix=doc.key_prefix,
            scopes=doc.scopes,
            expires_at=doc.expires_at,
            status=doc.status,
            id=str(doc.id),
            created_at=doc.created_at,
            updated_at=doc.updated_at
        )

    @staticmethod
    def api_key_to_document(domain: ApiKey) -> ApiKeyDocument:
        return ApiKeyDocument(
            org_id=domain.org_id,
            user_id=domain.user_id,
            name=domain.name,
            key_hash=domain.key_hash,
            key_prefix=domain.key_prefix,
            scopes=domain.scopes,
            expires_at=domain.expires_at,
            status=domain.status,
            created_at=domain.created_at,
            updated_at=domain.updated_at
        )

    # ==========================================================================
    # RefreshToken mappings
    # ==========================================================================
    @staticmethod
    def refresh_token_to_domain(doc: RefreshTokenDocument) -> RefreshToken:
        return RefreshToken(
            org_id=doc.org_id,
            user_id=doc.user_id,
            token_hash=doc.token_hash,
            expires_at=doc.expires_at,
            is_revoked=doc.is_revoked,
            replaced_by=doc.replaced_by,
            device_info=doc.device_info,
            id=str(doc.id),
            created_at=doc.created_at,
            updated_at=doc.updated_at
        )

    @staticmethod
    def refresh_token_to_document(domain: RefreshToken) -> RefreshTokenDocument:
        return RefreshTokenDocument(
            org_id=domain.org_id,
            user_id=domain.user_id,
            token_hash=domain.token_hash,
            expires_at=domain.expires_at,
            is_revoked=domain.is_revoked,
            replaced_by=domain.replaced_by,
            device_info=domain.device_info,
            created_at=domain.created_at,
            updated_at=domain.updated_at
        )
