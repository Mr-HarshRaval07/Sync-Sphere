from typing import Optional
from beanie import PydanticObjectId
from syncsphere.identity.domain.repositories.org_repository import OrgRepository
from syncsphere.identity.domain.entities.organization import Organization
from syncsphere.identity.infrastructure.documents.org_document import OrgDocument
from syncsphere.identity.infrastructure.mappers import IdentityMappers

class MongoOrgRepository(OrgRepository):
    """Concrete Mongo repository implementing OrgRepository interface using Beanie ODM."""

    async def save(self, org: Organization) -> None:
        doc = IdentityMappers.org_to_document(org)
        if org.id:
            try:
                existing_doc = await OrgDocument.get(PydanticObjectId(org.id))
                if existing_doc:
                    existing_doc.name = doc.name
                    existing_doc.slug = doc.slug
                    existing_doc.billing_tier = doc.billing_tier
                    existing_doc.quotas = doc.quotas
                    existing_doc.settings = doc.settings
                    existing_doc.feature_flags = doc.feature_flags
                    await existing_doc.save()
                    return
            except Exception:
                pass
        await doc.insert()
        org.id = str(doc.id)

    async def get_by_id(self, org_id: str) -> Optional[Organization]:
        try:
            doc = await OrgDocument.get(PydanticObjectId(org_id))
            return IdentityMappers.org_to_domain(doc) if doc else None
        except Exception:
            return None

    async def get_by_slug(self, slug: str) -> Optional[Organization]:
        doc = await OrgDocument.find_one(OrgDocument.slug == slug.lower().strip())
        return IdentityMappers.org_to_domain(doc) if doc else None
