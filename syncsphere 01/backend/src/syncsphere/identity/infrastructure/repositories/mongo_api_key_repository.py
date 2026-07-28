from typing import Optional, List
from beanie import PydanticObjectId
from syncsphere.identity.domain.repositories.api_key_repository import ApiKeyRepository
from syncsphere.identity.domain.entities.api_key import ApiKey
from syncsphere.identity.infrastructure.documents.api_key_document import ApiKeyDocument
from syncsphere.identity.infrastructure.mappers import IdentityMappers

class MongoApiKeyRepository(ApiKeyRepository):
    """Concrete Mongo repository implementing ApiKeyRepository interface using Beanie ODM."""

    async def save(self, api_key: ApiKey) -> None:
        doc = IdentityMappers.api_key_to_document(api_key)
        if api_key.id:
            try:
                existing_doc = await ApiKeyDocument.get(PydanticObjectId(api_key.id))
                if existing_doc:
                    existing_doc.name = doc.name
                    existing_doc.status = doc.status
                    existing_doc.scopes = doc.scopes
                    existing_doc.expires_at = doc.expires_at
                    await existing_doc.save()
                    return
            except Exception:
                pass
        await doc.insert()
        api_key.id = str(doc.id)

    async def get_by_id(self, key_id: str) -> Optional[ApiKey]:
        try:
            doc = await ApiKeyDocument.get(PydanticObjectId(key_id))
            return IdentityMappers.api_key_to_domain(doc) if doc else None
        except Exception:
            return None

    async def get_by_hash(self, key_hash: str) -> Optional[ApiKey]:
        doc = await ApiKeyDocument.find_one(ApiKeyDocument.key_hash == key_hash)
        return IdentityMappers.api_key_to_domain(doc) if doc else None

    async def list_by_user(self, org_id: str, user_id: str) -> List[ApiKey]:
        docs = await ApiKeyDocument.find(
            ApiKeyDocument.org_id == org_id,
            ApiKeyDocument.user_id == user_id
        ).to_list()
        return [IdentityMappers.api_key_to_domain(doc) for doc in docs]
