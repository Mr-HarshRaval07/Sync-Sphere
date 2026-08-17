from pydantic import BaseModel

class ConnectorConfig(BaseModel):
    """External MCP connector defaults and rate limits."""
    rate_limit_requests_per_minute: int = 60
