from typing import Optional, List
from beanie import PydanticObjectId
from syncsphere.identity.domain.repositories.role_repository import RoleRepository
from syncsphere.identity.domain.entities.role import Role
from syncsphere.identity.infrastructure.documents.role_document import RoleDocument
from syncsphere.identity.infrastructure.mappers import IdentityMappers

class MongoRoleRepository(RoleRepository):
    """Concrete Mongo repository implementing RoleRepository interface using Beanie ODM."""

    async def save(self, role: Role) -> None:
        doc = IdentityMappers.role_to_document(role)
        if role.id:
            try:
                existing_doc = await RoleDocument.get(PydanticObjectId(role.id))
                if existing_doc:
                    existing_doc.name = doc.name
                    existing_doc.description = doc.description
                    existing_doc.is_system_role = doc.is_system_role
                    existing_doc.permissions = doc.permissions
                    await existing_doc.save()
                    return
            except Exception:
                pass
        await doc.insert()
        role.id = str(doc.id)

    async def get_by_id(self, role_id: str) -> Optional[Role]:
        try:
            doc = await RoleDocument.get(PydanticObjectId(role_id))
            return IdentityMappers.role_to_domain(doc) if doc else None
        except Exception:
            return None

    async def get_by_name(self, org_id: str, name: str) -> Optional[Role]:
        doc = await RoleDocument.find_one(
            RoleDocument.org_id == org_id,
            RoleDocument.name == name
        )
        return IdentityMappers.role_to_domain(doc) if doc else None

    async def list_by_org(self, org_id: str) -> List[Role]:
        docs = await RoleDocument.find(RoleDocument.org_id == org_id).to_list()
        return [IdentityMappers.role_to_domain(doc) for doc in docs]

    async def delete(self, role_id: str) -> None:
        try:
            doc = await RoleDocument.get(PydanticObjectId(role_id))
            if doc:
                await doc.delete()
        except Exception:
            pass
