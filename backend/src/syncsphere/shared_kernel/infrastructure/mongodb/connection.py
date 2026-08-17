import logging
from motor.motor_asyncio import AsyncIOMotorClient
from syncsphere.core.config.settings import settings
from beanie import init_beanie
from typing import List, Any,Optional
from syncsphere.core.config.settings import settings
from syncsphere.identity.infrastructure.documents.user_document import UserDocument
logger = logging.getLogger("syncsphere.shared_kernel.infrastructure.mongodb")

class MongoDBConnectionManager:
    """
    Manages MongoDB connection lifecycle and Beanie initialization.
    Configures Motor client parameters such as pool sizes and connection limits.
    """
    
    def __init__(self) -> None:
        self.client: Optional[AsyncIOMotorClient] = None
        self.db: Optional[Any] = None

    async def connect(self, document_models: List[Any]) -> None:
        """
        Connects to MongoDB and initializes Beanie ODM with the specified document models.
        """
        try:
            logger.info("Final MongoDB URI received: %s", repr(settings.mongodb_uri))
            self.client = AsyncIOMotorClient(
                settings.mongodb_uri,
                maxPoolSize=settings.mongodb_max_pool_size,
                minPoolSize=10,
                uuidRepresentation="standard"
            )
            self.db = self.client[settings.mongodb_database]
            
            logger.info("Initializing Beanie ODM with %d document models", len(document_models))
            await init_beanie(
                database=self.db,
                document_models=document_models
            )
            logger.info("MongoDB and Beanie ODM initialized successfully.")
        except Exception as e:
            logger.error("Failed to connect to MongoDB / initialize Beanie: %s", str(e), exc_info=True)
            if getattr(settings, "mongodb_require_available", True):
                raise e
            logger.warning("Continuing startup without MongoDB (mongodb_require_available=false).")
            return


    async def disconnect(self) -> None:
        """Closes MongoDB connection."""
        if self.client:
            logger.info("Closing MongoDB connection client...")
            self.client.close()
            logger.info("MongoDB connection closed.")

# Singleton instance of MongoDB connection manager
mongodb_manager = MongoDBConnectionManager()

