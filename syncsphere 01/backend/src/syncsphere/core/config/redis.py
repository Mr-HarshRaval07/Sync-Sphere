from pydantic import BaseModel

class RedisConfig(BaseModel):
    """Redis connection and pooling settings."""
    uri: str = "redis://localhost:6379/0"
    max_connections: int = 50
