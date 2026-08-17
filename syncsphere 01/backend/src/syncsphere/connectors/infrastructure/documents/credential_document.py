from pydantic import Field
from typing import Dict
from syncsphere.shared_kernel.infrastructure.mongodb.base_document import BaseTenantDocument

class ConnectorCredentialDocument(BaseTenantDocument):
    """Beanie ODM representation of the ConnectorCredential entity."""
    connector_id: str = Field(..., description="Linked connector primary identifier")
    encrypted_secrets: Dict[str, str] = Field(default_factory=dict, description="Map of encrypted config keys and values")

    class Settings:
        name = "connector_credentials"
        indexes = [
            "org_id",
            ("org_id", "connector_id")
        ]
