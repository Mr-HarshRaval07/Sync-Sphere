from syncsphere.connectors.domain.entities.connector import Connector
from syncsphere.connectors.domain.entities.credential import ConnectorCredential
from syncsphere.connectors.domain.value_objects import (
    ToolDefinition,
    ConnectorLimits,
    ConnectorPermissions,
    ConnectorHealth,
)
from syncsphere.connectors.infrastructure.documents.connector_document import (
    ConnectorDocument,
    ToolDefinitionEmbed,
    ConnectorLimitsEmbed,
    ConnectorPermissionsEmbed,
    ConnectorHealthEmbed,
)
from syncsphere.connectors.infrastructure.documents.credential_document import ConnectorCredentialDocument

class ConnectorMappers:
    """Utility conversions between Connector Domain models and Beanie Documents."""

    @staticmethod
    def connector_to_domain(doc: ConnectorDocument) -> Connector:
        tools = [
            ToolDefinition(
                name=t.name,
                description=t.description,
                input_schema=t.input_schema
            ) for t in doc.tools
        ]
        limits = ConnectorLimits(
            max_requests_per_minute=doc.limits.max_requests_per_minute,
            max_concurrency=doc.limits.max_concurrency,
            timeout_seconds=doc.limits.timeout_seconds
        )
        permissions = ConnectorPermissions(
            required_scopes=doc.permissions.required_scopes,
            user_roles_allowed=doc.permissions.user_roles_allowed
        )
        health = ConnectorHealth(
            status=doc.health.status,
            latency_ms=doc.health.latency_ms,
            last_checked=doc.health.last_checked,
            error_message=doc.health.error_message
        )
        return Connector(
            org_id=doc.org_id,
            name=doc.name,
            transport_type=doc.transport_type,
            connection_config=doc.connection_config,
            status=doc.status,
            tools=tools,
            limits=limits,
            permissions=permissions,
            health=health,
            id=str(doc.id),
            created_at=doc.created_at,
            updated_at=doc.updated_at
        )

    @staticmethod
    def connector_to_document(domain: Connector) -> ConnectorDocument:
        tools = [
            ToolDefinitionEmbed(
                name=t.name,
                description=t.description,
                input_schema=t.input_schema
            ) for t in domain.tools
        ]
        limits = ConnectorLimitsEmbed(
            max_requests_per_minute=domain.limits.max_requests_per_minute,
            max_concurrency=domain.limits.max_concurrency,
            timeout_seconds=domain.limits.timeout_seconds
        )
        permissions = ConnectorPermissionsEmbed(
            required_scopes=domain.permissions.required_scopes,
            user_roles_allowed=domain.permissions.user_roles_allowed
        )
        health = ConnectorHealthEmbed(
            status=domain.health.status,
            latency_ms=domain.health.latency_ms,
            last_checked=domain.health.last_checked,
            error_message=domain.health.error_message
        )
        return ConnectorDocument(
            org_id=domain.org_id,
            name=domain.name,
            transport_type=domain.transport_type,
            connection_config=domain.connection_config,
            status=domain.status,
            tools=tools,
            limits=limits,
            permissions=permissions,
            health=health,
            created_at=domain.created_at,
            updated_at=domain.updated_at
        )

    @staticmethod
    def credential_to_domain(doc: ConnectorCredentialDocument) -> ConnectorCredential:
        return ConnectorCredential(
            org_id=doc.org_id,
            connector_id=doc.connector_id,
            encrypted_secrets=doc.encrypted_secrets,
            id=str(doc.id),
            created_at=doc.created_at,
            updated_at=doc.updated_at
        )

    @staticmethod
    def credential_to_document(domain: ConnectorCredential) -> ConnectorCredentialDocument:
        return ConnectorCredentialDocument(
            org_id=domain.org_id,
            connector_id=domain.connector_id,
            encrypted_secrets=domain.encrypted_secrets,
            created_at=domain.created_at,
            updated_at=domain.updated_at
        )
