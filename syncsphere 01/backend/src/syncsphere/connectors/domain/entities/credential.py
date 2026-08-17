from typing import Dict, Optional
from syncsphere.shared_kernel.domain.entity import Entity

class ConnectorCredential(Entity):
    """
    ConnectorCredential domain entity representing encrypted connection keys
    (API tokens, passwords, private keys) linked to an MCP connector.
    """
    
    def __init__(
        self,
        org_id: str,
        connector_id: str,
        encrypted_secrets: Dict[str, str],
        id: Optional[str] = None,
        **kwargs
    ) -> None:
        super().__init__(id=id, **kwargs)
        self.org_id = org_id
        self.connector_id = connector_id
        
        # encrypted_secrets maps config keys (e.g. "API_KEY") to encrypted ciphertext strings
        self.encrypted_secrets = encrypted_secrets

    def update_secrets(self, new_encrypted_secrets: Dict[str, str]) -> None:
        """Updates the encrypted secrets dictionary."""
        self.encrypted_secrets.update(new_encrypted_secrets)
