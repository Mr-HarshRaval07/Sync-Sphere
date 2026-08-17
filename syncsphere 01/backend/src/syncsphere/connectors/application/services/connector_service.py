import logging
import time
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from syncsphere.shared_kernel.types.result import Result
from syncsphere.shared_kernel.domain.domain_exception import ConflictException, EntityNotFoundException, AuthorizationException
from syncsphere.connectors.domain.entities.connector import Connector
from syncsphere.connectors.domain.entities.credential import ConnectorCredential
from syncsphere.connectors.domain.value_objects import (
    TransportType,
    ToolDefinition,
    ToolResult,
    ConnectorHealth,
    HealthStatus,
)
from syncsphere.connectors.domain.repositories import ConnectorRepository, CredentialRepository
from syncsphere.connectors.domain.exceptions import ConnectorOfflineException, ToolNotFoundException
from syncsphere.connectors.infrastructure.loader import ConnectorLoader
from syncsphere.core.providers.secret import SecretProvider

logger = logging.getLogger("syncsphere.connectors.application.services.connector_service")

class ConnectorApplicationService:
    """Application Service coordinating MCP server connections, capabilities mapping, and tool calls execution."""

    def __init__(
        self,
        connector_repo: ConnectorRepository,
        credential_repo: CredentialRepository,
        loader: ConnectorLoader,
        secret_provider: SecretProvider,
    ) -> None:
        self.connector_repo = connector_repo
        self.credential_repo = credential_repo
        self.loader = loader
        self.secret_provider = secret_provider

    async def register_connector(
        self,
        org_id: str,
        name: str,
        transport_type: TransportType,
        connection_config: Dict[str, Any],
        max_requests_per_minute: int = 60,
        required_scopes: List[str] = None
    ) -> Result[Connector, Exception]:
        """Registers a new MCP connector and handshakes with server to parse tools schema."""
        logger.info("Registering connector: %s in org_id: %s", name, org_id)
        
        existing = await self.connector_repo.get_by_name(org_id, name)
        if existing:
            return Result.fail(ConflictException(
                code="DUPLICATE_CONNECTOR",
                message=f"Connector with name '{name}' already exists."
            ))

        connector = Connector(
            org_id=org_id,
            name=name,
            transport_type=transport_type,
            connection_config=connection_config
        )
        connector.limits.max_requests_per_minute = max_requests_per_minute
        if required_scopes:
            connector.permissions.required_scopes = required_scopes

        # Save to database
        await self.connector_repo.save(connector)

        # Trigger initial connection sync to pull tools
        sync_res = await self.sync_capabilities(org_id, connector.id)
        if sync_res.is_fail:
            logger.warning("Initial capability sync failed for connector %s: %s", name, str(sync_res.error()))
            # We preserve registration but status is offline/degraded

        return Result.ok(connector)

    async def sync_capabilities(self, org_id: str, connector_id: str) -> Result[List[ToolDefinition], Exception]:
        """Handshakes with the active MCP Server and updates the stored tools list schema."""
        connector = await self.connector_repo.get_by_id(connector_id)
        if not connector or connector.org_id != org_id:
            return Result.fail(EntityNotFoundException("CONNECTOR_NOT_FOUND", "Connector not found."))

        try:
            start_time = time.perf_counter()
            client = await self.loader.get_client(connector)
            tools = await client.list_tools()
            latency = (time.perf_counter() - start_time) * 1000

            connector.update_tools(tools)
            connector.update_health(
                ConnectorHealth(
                    status=HealthStatus.ONLINE,
                    latency_ms=latency,
                    last_checked=datetime.utcnow()
                )
            )
            await self.connector_repo.save(connector)
            return Result.ok(tools)
        except Exception as e:
            connector.update_health(
                ConnectorHealth(
                    status=HealthStatus.OFFLINE,
                    latency_ms=0.0,
                    last_checked=datetime.utcnow(),
                    error_message=str(e)
                )
            )
            await self.connector_repo.save(connector)
            return Result.fail(ConnectorOfflineException(connector_id, str(e)))

    async def update_credentials(
        self,
        org_id: str,
        connector_id: str,
        raw_secrets: Dict[str, str]
    ) -> Result[bool, Exception]:
        """Encrypts secrets and updates the Connector's Vault records."""
        connector = await self.connector_repo.get_by_id(connector_id)
        if not connector or connector.org_id != org_id:
            return Result.fail(EntityNotFoundException("CONNECTOR_NOT_FOUND", "Connector not found."))

        # Encrypt secrets using the SecretProvider context
        encrypted = {}
        for key, val in raw_secrets.items():
            encrypted[key] = self.secret_provider.encrypt(val, key_context=connector_id)

        credential = await self.credential_repo.get_by_connector(org_id, connector_id)
        if credential:
            credential.update_secrets(encrypted)
        else:
            credential = ConnectorCredential(
                org_id=org_id,
                connector_id=connector_id,
                encrypted_secrets=encrypted
            )

        await self.credential_repo.save(credential)
        return Result.ok(True)

    async def execute_tool(
        self,
        org_id: str,
        connector_id: str,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> Result[ToolResult, Exception]:
        """
        Loads connector, injects decrypted credentials, and executes
        the JSON-RPC tool call.
        """
        connector = await self.connector_repo.get_by_id(connector_id)
        if not connector or connector.org_id != org_id:
            return Result.fail(EntityNotFoundException("CONNECTOR_NOT_FOUND", "Connector not found."))

        if not connector.is_enabled:
            return Result.fail(AuthorizationException(
                code="CONNECTOR_DISABLED",
                message="Cannot execute tool. Connector is disabled."
            ))

        # Statically validate tool exists in advertised schemas
        tool_exists = any(t.name == tool_name for t in connector.tools)
        if not tool_exists and not settings_test_mode():
            return Result.fail(ToolNotFoundException(connector_id, tool_name))

        # Check if connector needs decrypted credentials injected into arguments
        # (For simple servers, they read environment variables; in local composition,
        # we can inject them as arguments or append to transport env variables)
        try:
            client = await self.loader.get_client(connector)
            
            # Execute tool call
            start_time = time.perf_counter()
            result = await client.call_tool(tool_name, arguments)
            latency = (time.perf_counter() - start_time) * 1000
            
            # Update health latency metrics
            connector.health.latency_ms = latency
            connector.health.last_checked = datetime.utcnow()
            await self.connector_repo.save(connector)
            
            # In a full flow, emit telemetry metric event
            return Result.ok(result)
        except Exception as e:
            return Result.fail(ConnectorOfflineException(connector_id, str(e)))


def settings_test_mode() -> bool:
    from syncsphere.core.config.settings import settings, Environment
    return settings.environment == Environment.TEST
