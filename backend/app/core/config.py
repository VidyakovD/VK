from functools import lru_cache
from typing import Any, Literal

from pydantic import Field, PostgresDsn, RedisDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    env: Literal["development", "staging", "production"] = "development"
    debug: bool = True
    log_level: str = "INFO"
    tz: str = "Europe/Moscow"

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_public_url: str = "http://localhost:8000"
    frontend_url: str = "http://localhost:5173"

    # Security
    jwt_secret: str = Field(min_length=16)
    jwt_access_ttl_seconds: int = 3600
    jwt_refresh_ttl_seconds: int = 2592000
    token_encryption_key: str = Field(min_length=16)

    # Database
    database_url: PostgresDsn

    # Redis
    redis_url: RedisDsn
    celery_broker_url: str
    celery_result_backend: str

    # Qdrant
    qdrant_url: str = "http://qdrant:6333"
    qdrant_api_key: str | None = None

    # S3
    s3_endpoint_url: str = "https://storage.yandexcloud.net"
    s3_region: str = "ru-central1"
    s3_access_key_id: str | None = None
    s3_secret_access_key: str | None = None
    s3_bucket: str = "vk-saas-media"

    # VK Mini App
    vk_app_id: int | None = None
    vk_app_secure_key: str | None = None
    vk_app_service_token: str | None = None

    # OpenAI
    openai_api_key: str | None = None
    openai_model_dialog: str = "gpt-4o"
    openai_model_embedding: str = "text-embedding-3-small"
    openai_model_image: str = "gpt-image-2"

    # Anthropic
    anthropic_api_key: str | None = None
    anthropic_model_dialog: str = "claude-sonnet-4-6"

    # Proxy for outbound LLM calls
    http_proxy: str | None = None
    https_proxy: str | None = None

    # ЮKassa
    yookassa_shop_id: str | None = None
    yookassa_secret_key: str | None = None
    yookassa_webhook_secret: str | None = None

    # Observability
    sentry_dsn: str | None = None
    prometheus_enabled: bool = True

    @field_validator("vk_app_id", mode="before")
    @classmethod
    def _empty_string_as_none(cls, v: Any) -> Any:
        """Treat empty string env values as None for optional non-string fields."""
        if isinstance(v, str) and v.strip() == "":
            return None
        return v

    @property
    def is_production(self) -> bool:
        return self.env == "production"

    @property
    def sync_database_url(self) -> str:
        """Sync URL for Alembic (no +asyncpg)."""
        url = str(self.database_url)
        return url.replace("postgresql+asyncpg://", "postgresql://")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]


settings = get_settings()
