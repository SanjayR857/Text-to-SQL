"""
Centralised application configuration using pydantic-settings.

All settings are loaded from environment variables and/or the .env file.
Sensitive values are wrapped in SecretStr to prevent leakage in logs or traces.
The settings object is a cached singleton via @lru_cache.

Field naming convention:
  - Field names are lowercase (Pythonic, PEP 8).
  - pydantic-settings maps them automatically to their UPPERCASE env var equivalents
    because case_sensitive=False. Example: database_url -> DATABASE_URL in .env
"""
from functools import lru_cache
from typing import Literal, Self

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # -------------------------------------------------------------------------
    # Application
    # Env vars: APP_NAME, APP_VERSION, ENVIRONMENT, DEBUG
    # -------------------------------------------------------------------------
    app_name: str = "Enterprise Agentic Text-to-SQL"
    app_version: str = "1.0.0"
    environment: Literal["development", "staging", "production", "testing"] = "development"
    debug: bool = False
    # Development authentication header enablement (x-dev-user-email): strictly forbidden in production
    allow_dev_auth: bool = False

    @model_validator(mode="after")
    def validate_dev_auth_safety(self) -> Self:
        """Enforce that development authentication is strictly forbidden in production."""
        if self.is_production and self.allow_dev_auth:
            raise ValueError(
                "Security violation: ALLOW_DEV_AUTH must not be enabled in production environments."
            )
        return self

    # -------------------------------------------------------------------------
    # Primary Database
    # Env vars: DATABASE_URL, CHECKPOINT_DATABASE_URL
    # -------------------------------------------------------------------------
    database_url: SecretStr
    # Isolated database for LangGraph checkpoint persistence
    checkpoint_database_url: SecretStr

    # Connection Pooling
    # Env vars: DB_POOL_SIZE, DB_MAX_OVERFLOW, DB_POOL_TIMEOUT
    db_pool_size: int = Field(default=5, ge=1, le=50)
    db_max_overflow: int = Field(default=5, ge=0, le=50)
    db_pool_timeout: int = Field(default=30, ge=1)

    # -------------------------------------------------------------------------
    # Azure OpenAI
    # Env vars: AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY,
    #           AZURE_OPENAI_API_VERSION, AZURE_OPENAI_CHAT_DEPLOYMENT,
    #           AZURE_OPENAI_EMBEDDING_DEPLOYMENT, EMBEDDING_DIMENSIONS
    # -------------------------------------------------------------------------
    azure_openai_endpoint: str
    # Optional — omit in production to authenticate via Azure Managed Identity
    azure_openai_api_key: SecretStr | None = None
    azure_openai_api_version: str = "2024-10-21"
    azure_openai_chat_deployment: str = "gpt-4o"
    azure_openai_mini_deployment: str = "gpt-4o-mini"
    azure_openai_embedding_deployment: str = "text-embedding-3-small"
    embedding_dimensions: int = 1536

    # -------------------------------------------------------------------------
    # Microsoft Entra ID
    # Env vars: ENTRA_TENANT_ID, ENTRA_API_AUDIENCE
    # -------------------------------------------------------------------------
    entra_tenant_id: str
    entra_api_audience: str

    # -------------------------------------------------------------------------
    # SQL Security & Execution Guardrails
    # Env vars: SQL_STATEMENT_TIMEOUT_MS, SQL_MAX_ROWS, SQL_MAX_RESPONSE_BYTES
    # -------------------------------------------------------------------------
    sql_statement_timeout_ms: int = Field(default=5000, ge=100)
    sql_max_rows: int = Field(default=1000, ge=1)
    sql_max_response_bytes: int = Field(default=1_000_000, ge=1024)

    # -------------------------------------------------------------------------
    # Redis & Observability
    # Env vars: REDIS_URL, LOG_LEVEL, APPLICATIONINSIGHTS_CONNECTION_STRING,
    #           OTEL_EXPORTER_OTLP_ENDPOINT, ENABLE_TELEMETRY
    # -------------------------------------------------------------------------
    redis_url: str = "redis://localhost:6379/0"
    log_level: str = "INFO"
    applicationinsights_connection_string: SecretStr | None = None
    otel_exporter_otlp_endpoint: str | None = None
    enable_telemetry: bool = True

    # -------------------------------------------------------------------------
    # Computed helpers (not env vars)
    # -------------------------------------------------------------------------
    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def is_development(self) -> bool:
        return self.environment == "development"

    @property
    def APP_NAME(self) -> str:
        return self.app_name

    @property
    def APP_VERSION(self) -> str:
        return self.app_version

    @property
    def cors_origins(self) -> list[str]:
        return ["*"]


@lru_cache
def get_settings() -> Settings:
    """Return a cached singleton instance of application settings."""
    return Settings()


# Module-level singleton — import and use directly in application code:
#   from core.config import settings
#
# Use get_settings as a FastAPI dependency for DI-friendly injection:
#   from core.config import get_settings
#   def my_route(cfg: Annotated[Settings, Depends(get_settings)]): ...
settings = get_settings()
