from typing import Optional, List

from beanie import PydanticObjectId

from syncsphere.connectors.domain.repositories.connector_repository import (
    ConnectorRepository,
)

from syncsphere.connectors.domain.entities.connector import (
    Connector,
)

from syncsphere.connectors.infrastructure.documents.connector_document import (
    ConnectorDocument,
)

from syncsphere.connectors.infrastructure.mappers import (
    ConnectorMappers,
)


class MongoConnectorRepository(ConnectorRepository):
    """Concrete Mongo repository implementing ConnectorRepository using Beanie ODM."""

    async def save(self, connector: Connector) -> None:
        doc = ConnectorMappers.connector_to_document(connector)

        if connector.id:
            try:
                existing_doc = await ConnectorDocument.get(
                    PydanticObjectId(connector.id)
                )

                if existing_doc:
                    existing_doc.name = doc.name
                    existing_doc.transport_type = doc.transport_type
                    existing_doc.status = doc.status
                    existing_doc.tools = doc.tools
                    existing_doc.limits = doc.limits
                    existing_doc.permissions = doc.permissions
                    existing_doc.health = doc.health
                    existing_doc.connection_config = (
                        doc.connection_config
                    )

                    await existing_doc.save()
                    return

            except Exception:
                pass

        await doc.insert()
        connector.id = str(doc.id)

    async def get_by_id(
        self,
        connector_id: str,
    ) -> Optional[Connector]:

        try:
            doc = await ConnectorDocument.get(
                PydanticObjectId(connector_id)
            )

            return (
                ConnectorMappers.connector_to_domain(doc)
                if doc
                else None
            )

        except Exception:
            return None

    async def get_by_name(
        self,
        org_id: str,
        name: str,
    ) -> Optional[Connector]:

        doc = await ConnectorDocument.find_one(
            ConnectorDocument.org_id == org_id,
            ConnectorDocument.name == name.lower().strip(),
        )

        return (
            ConnectorMappers.connector_to_domain(doc)
            if doc
            else None
        )

    async def list_by_org(
        self,
        org_id: str,
    ) -> List[Connector]:

        docs = await ConnectorDocument.find(
            ConnectorDocument.org_id == org_id
        ).to_list()

        return [
            ConnectorMappers.connector_to_domain(doc)
            for doc in docs
        ]

    async def delete(
        self,
        connector_id: str,
    ) -> None:

        try:
            doc = await ConnectorDocument.get(
                PydanticObjectId(connector_id)
            )

            if doc:
                await doc.delete()

        except Exception:
            pass