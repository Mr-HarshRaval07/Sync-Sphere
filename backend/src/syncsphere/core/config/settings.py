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
    github_client_id: str = Field(default="", validation_alias="GITHUB_CLIENT_ID")
    github_client_secret: str = Field(default="", validation_alias="GITHUB_CLIENT_SECRET")
    github_redirect_uri: str = Field(default="http://localhost:8000/v1/connect/github/callback", validation_alias="GITHUB_REDIRECT_URI")

    # Slack OAuth
    slack_client_id: str = Field(default="", validation_alias="SLACK_CLIENT_ID")
    slack_client_secret: str = Field(default="", validation_alias="SLACK_CLIENT_SECRET")
    slack_signing_secret: str = Field(default="", validation_alias="SLACK_SIGNING_SECRET")
    slack_redirect_uri: str = Field(default="http://localhost:8000/v1/connect/slack/callback", validation_alias="SLACK_REDIRECT_URI")
    slack_default_channel: str = Field(default="#all-janhvi", validation_alias="SLACK_DEFAULT_CHANNEL")
    slack_bot_token: str = Field(default="", validation_alias="SLACK_BOT_TOKEN")

    # notion auth
    notion_client_id: str = Field(default="", validation_alias="NOTION_CLIENT_ID")
    notion_client_secret: str = Field(default="", validation_alias="NOTION_CLIENT_SECRET")
    notion_redirect_uri: str = Field(default="http://localhost:8000/v1/connect/notion/callback", validation_alias="NOTION_REDIRECT_URI")
    notion_auth_url: str = "https://api.notion.com/v1/oauth/authorize"
    notion_token_url: str = "https://api.notion.com/v1/oauth/token"
    notion_api_base_url: str = "https://api.notion.com/v1"
    notion_api_version: str = "2026-03-11"

    # jira auth
    jira_client_id: str = Field(default="", validation_alias="JIRA_CLIENT_ID")
    jira_client_secret: str = Field(default="", validation_alias="JIRA_CLIENT_SECRET")
    jira_redirect_uri: str = Field(default="http://localhost:8000/v1/connect/jira/callback", validation_alias="JIRA_REDIRECT_URI")

    # google auth
    google_client_id: str = Field(default="", validation_alias="GOOGLE_CLIENT_ID")
    google_client_secret: str = Field(default="", validation_alias="GOOGLE_CLIENT_SECRET")
    google_redirect_uri: str = Field(default="http://localhost:8000/v1/connect/google/callback", validation_alias="GOOGLE_REDIRECT_URI")

    frontend_url: str = Field(default="http://localhost:3000", validation_alias="FRONTEND_URL")
    backend_url: str = Field(default="http://localhost:8000", validation_alias="BACKEND_URL")

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
    jwt_access_token_ttl: int = 86400
    jwt_refresh_token_ttl: int = 604800

    master_encryption_key: SecretStr = Field(
        default="z7pQYv_3e8q56_u-j-2W1S3K6L8_9x1v_3e8q56_u-I="
    )

    # ------------------------------------------------------------------
    # AI Config Mapping
    # ------------------------------------------------------------------
    llm_provider: str = "openrouter"
    llm_api_key: SecretStr = Field(default="mock-api-key-for-local-dev")
    llm_model: str = "inclusionai/ling-3.0-tiny:free"
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