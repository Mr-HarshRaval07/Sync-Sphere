from typing import Optional
from beanie import PydanticObjectId
from syncsphere.identity.domain.repositories.refresh_token_repository import RefreshTokenRepository
from syncsphere.identity.domain.entities.refresh_token import RefreshToken
from syncsphere.identity.infrastructure.documents.refresh_token_document import RefreshTokenDocument
from syncsphere.identity.infrastructure.mappers import IdentityMappers

class MongoRefreshTokenRepository(RefreshTokenRepository):
    """Concrete Mongo repository implementing RefreshTokenRepository interface using Beanie ODM."""

    async def save(self, token: RefreshToken) -> None:
        doc = IdentityMappers.refresh_token_to_document(token)
        if token.id:
            try:
                existing_doc = await RefreshTokenDocument.get(PydanticObjectId(token.id))
                if existing_doc:
                    existing_doc.is_revoked = doc.is_revoked
                    existing_doc.replaced_by = doc.replaced_by
                    await existing_doc.save()
                    return
            except Exception:
                pass
        await doc.insert()
        token.id = str(doc.id)

    async def get_by_hash(self, token_hash: str) -> Optional[RefreshToken]:
        doc = await RefreshTokenDocument.find_one(RefreshTokenDocument.token_hash == token_hash)
        return IdentityMappers.refresh_token_to_domain(doc) if doc else None

    async def revoke_all_for_user(self, user_id: str) -> None:
        # Fetch and mark all tokens as revoked in bulk
        await RefreshTokenDocument.find(
            RefreshTokenDocument.user_id == user_id,
            RefreshTokenDocument.is_revoked == False
        ).update({"$set": {"is_revoked": True}})
