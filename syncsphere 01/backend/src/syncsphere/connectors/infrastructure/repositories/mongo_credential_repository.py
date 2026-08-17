from typing import Optional
from beanie import PydanticObjectId
from syncsphere.connectors.domain.repositories.credential_repository import CredentialRepository
from syncsphere.connectors.domain.entities.credential import ConnectorCredential
from syncsphere.connectors.infrastructure.documents.credential_document import ConnectorCredentialDocument
from syncsphere.connectors.infrastructure.mappers import ConnectorMappers

class MongoCredentialRepository(CredentialRepository):
    """Concrete Mongo repository implementing CredentialRepository using Beanie ODM."""

    async def save(self, credential: ConnectorCredential) -> None:
        doc = ConnectorMappers.credential_to_document(credential)
        if credential.id:
            try:
                existing_doc = await ConnectorCredentialDocument.get(PydanticObjectId(credential.id))
                if existing_doc:
                    existing_doc.encrypted_secrets = doc.encrypted_secrets
                    await existing_doc.save()
                    return
            except Exception:
                pass
        await doc.insert()
        credential.id = str(doc.id)

    async def get_by_connector(self, org_id: str, connector_id: str) -> Optional[ConnectorCredential]:
        doc = await ConnectorCredentialDocument.find_one(
            ConnectorCredentialDocument.org_id == org_id,
            ConnectorCredentialDocument.connector_id == connector_id
        )
        return ConnectorMappers.credential_to_domain(doc) if doc else None

    async def delete(self, org_id: str, connector_id: str) -> None:
        doc = await ConnectorCredentialDocument.find_one(
            ConnectorCredentialDocument.org_id == org_id,
            ConnectorCredentialDocument.connector_id == connector_id
        )
        if doc:
            await doc.delete()
