from enum import Enum
from pydantic import BaseModel

class Environment(str, Enum):
    LOCAL = "local"
    TEST = "test"
    STAGING = "staging"
    PRODUCTION = "production"

class AppConfig(BaseModel):
    """General application settings."""
    name: str = "SyncSphere AI"
    environment: Environment = Environment.LOCAL
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 1
