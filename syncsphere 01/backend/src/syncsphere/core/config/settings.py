from pathlib import Path
import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, SecretStr

from .app import AppConfig, Environment
from .database import DatabaseConfig
from .redis import RedisConfig
from .security import SecurityConfig
from .logging import LoggingConfig
from .ai import AIConfig
from .execution import ExecutionConfig
from .connector import ConnectorConfig

# Project root:
# backend/src/syncsphere/core/config/settings.py
#                               ↑
# parents[5] => syncsphere 01/
BASE_DIR = Path(__file__).resolve().parents[4]

import os

print(os.getenv("SYNCSPHERE_MONGODB_URI"))
print(BASE_DIR)
print(BASE_DIR / ".env")
print((BASE_DIR / ".env").exists())
class Settings(BaseSettings):
    """
    Unified settings manager aggregating modular config instances.
    Maps environment variables prefixed with 'SYNCSPHERE_' to specific attributes.
    """

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        env_prefix="SYNCSPHERE_",
        case_sensitive=False,
        extra="ignore",
    )
    github_client_id: str = "Ov23lilGnliV2TU5iDAu"
    github_client_secret: str = "756f72fa6e80e7ab3192a0d3bd016810ce03a081"
    # Must match the backend route mounted as: /v1 + /connect/github/callback
    github_redirect_uri: str = "http://localhost:8000/v1/connect/github/callback"
    github_token: str = "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"
    github_owner: str = "Mr-HarshRaval07"
    github_repo: str = "Sync-Sphere"

    # Slack OAuth
    slack_client_id: str = "11431822026630.11444427248130"
    slack_client_secret: str = "6978575996c8267df7006e9e1e5e2593"
    slack_signing_secret: str = "2dfdbad054ecaebb20c57868942d6c6c"
    slack_redirect_uri: str = "http://localhost:8000/v1/connect/slack/callback"
    slack_default_channel: str = "#all-janhvi"
    slack_bot_token: str="xoxb-11431822026630-11444456709986-60qBXGdoNezjml2ODOC9zeUw"
    

    # google auth
    google_client_id:str="6505797365-597hacegrm39j1p2bl58ufgq37md2oj0.apps.googleusercontent.com"
    google_client_secret:str="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"
    google_redirect_uri:str="http://localhost:8000/v1/connect/google/callback"

    frontend_url: str = "http://localhost:3000"

    # ------------------------------------------------------------------
    # App Config Mapping
    # ------------------------------------------------------------------
    app_name: str = "SyncSphere AI"
    environment: Environment = Environment.LOCAL
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 1

    # ------------------------------------------------------------------
    # Database Config Mapping
    # ------------------------------------------------------------------
    # mongodb_uri: str = "mongodb://root:rootpassword@localhost:27017/syncsphere?authSource=admin"
    mongodb_uri: str
    mongodb_database: str = "syncsphere"
    mongodb_max_pool_size: int = 100
    # If false, backend will still start even if MongoDB is unavailable (dev-friendly).
    mongodb_require_available: bool = False


    # ------------------------------------------------------------------
    # Redis Config Mapping
    # ------------------------------------------------------------------
    redis_uri: str = "redis://localhost:6379/0"
    redis_max_connections: int = 50

    # ------------------------------------------------------------------
    # Security Config Mapping
    # ------------------------------------------------------------------
    jwt_secret: SecretStr = Field(
        default="supersecretjwtkeythatisthirtytwobyteslongtobesecure"
    )
    jwt_algorithm: str = "HS256"
    jwt_access_token_ttl: int = 900
    jwt_refresh_token_ttl: int = 604800

    master_encryption_key: SecretStr = Field(
        default="z7pQYv_3e8q56_u-j-2W1S3K6L8_9x1v_3e8q56_u-I="
    )

    # ------------------------------------------------------------------
    # AI Config Mapping
    # ------------------------------------------------------------------
    llm_provider: str = "openai"
    llm_api_key: SecretStr = Field(default="mock-api-key-for-local-dev")
    llm_model: str = "gpt-4o"
    llm_max_tokens: int = 4096

    embedding_provider: str = "openai"
    embedding_api_key: SecretStr = Field(default="mock-api-key-for-local-dev")
    embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 1536

    # ------------------------------------------------------------------
    # Execution Config Mapping
    # ------------------------------------------------------------------
    execution_default_timeout: int = 3600
    execution_max_retries: int = 3
    execution_checkpoint_enabled: bool = True

    feature_reflection_enabled: bool = True
    feature_approval_enabled: bool = True

    # ------------------------------------------------------------------
    # Connector Config Mapping
    # ------------------------------------------------------------------
    rate_limit_requests_per_minute: int = 60

    @property
    def app(self) -> AppConfig:
        return AppConfig(
            name=self.app_name,
            environment=self.environment,
            debug=self.debug,
            host=self.host,
            port=self.port,
            workers=self.workers,
        )

    @property
    def database(self) -> DatabaseConfig:
        return DatabaseConfig(
            uri=self.mongodb_uri,
            database=self.mongodb_database,
            max_pool_size=self.mongodb_max_pool_size,
        )

    @property
    def redis(self) -> RedisConfig:
        return RedisConfig(
            uri=self.redis_uri,
            max_connections=self.redis_max_connections,
        )

    @property
    def security(self) -> SecurityConfig:
        return SecurityConfig(
            jwt_secret=self.jwt_secret,
            jwt_algorithm=self.jwt_algorithm,
            jwt_access_token_ttl=self.jwt_access_token_ttl,
            jwt_refresh_token_ttl=self.jwt_refresh_token_ttl,
            master_encryption_key=self.master_encryption_key,
        )

    @property
    def logging(self) -> LoggingConfig:
        return LoggingConfig(
            level="DEBUG" if self.debug else "INFO",
            format_json=self.environment
            in (Environment.STAGING, Environment.PRODUCTION),
        )

    @property
    def ai(self) -> AIConfig:
        return AIConfig(
            llm_provider=self.llm_provider,
            llm_api_key=self.llm_api_key,
            llm_model=self.llm_model,
            llm_max_tokens=self.llm_max_tokens,
            embedding_provider=self.embedding_provider,
            embedding_api_key=self.embedding_api_key,
            embedding_model=self.embedding_model,
            embedding_dimensions=self.embedding_dimensions,
        )

    @property
    def execution(self) -> ExecutionConfig:
        return ExecutionConfig(
            default_timeout=self.execution_default_timeout,
            max_retries=self.execution_max_retries,
            checkpoint_enabled=self.execution_checkpoint_enabled,
            reflection_enabled=self.feature_reflection_enabled,
            approval_enabled=self.feature_approval_enabled,
        )

    @property
    def connector(self) -> ConnectorConfig:
        return ConnectorConfig(
            rate_limit_requests_per_minute=self.rate_limit_requests_per_minute,
        )


settings = Settings()