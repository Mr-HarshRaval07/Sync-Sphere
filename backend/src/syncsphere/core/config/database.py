from pydantic import BaseModel

class DatabaseConfig(BaseModel):
    """MongoDB/Beanie connection and pooling settings."""
    uri: str = "mongodb://root:rootpassword@localhost:27017/syncsphere?authSource=admin"
    database: str = "syncsphere"
    max_pool_size: int = 100
