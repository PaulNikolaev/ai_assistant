"""Application configuration loaded from environment variables.

Uses pydantic-settings to validate and expose all runtime settings.
DATABASE_URL, REDIS_URL, and QDRANT_URL are auto-constructed from
individual host/port/credentials fields when not provided explicitly.
"""

from typing import Literal

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── App ────────────────────────────────────────────────────────
    APP_ENV: Literal["development", "production", "testing"] = "development"

    # ── PostgreSQL ─────────────────────────────────────────────────
    POSTGRES_HOST: str = "postgres"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "ai_assistant"
    POSTGRES_USER: str = "ai_assistant"
    POSTGRES_PASSWORD: str = "changeme"
    DATABASE_URL: str = ""

    # ── Redis ──────────────────────────────────────────────────────
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = ""
    REDIS_URL: str = ""

    # ── Qdrant ────────────────────────────────────────────────────
    QDRANT_HOST: str = "qdrant"
    QDRANT_PORT: int = 6333
    QDRANT_URL: str = ""

    # ── MinIO ─────────────────────────────────────────────────────
    MINIO_ENDPOINT: str = "http://minio:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "changeme"
    MINIO_BUCKET: str = "ai-assistant"

    # ── JWT ───────────────────────────────────────────────────────
    JWT_SECRET: str = "dev-jwt-secret-change-in-production-min-32-chars"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # ── Encryption ────────────────────────────────────────────────
    # Generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
    ENCRYPTION_KEY: str = "dev-fernet-key-replace-before-production-deploy="

    # ── Internal secrets ──────────────────────────────────────────
    MESSENGERS_INTERNAL_SECRET: str = "dev-internal-secret-change-in-production"

    # ── CORS ──────────────────────────────────────────────────────
    # Comma-separated origins. HTTP is intentional for local dev (localhost).
    ALLOWED_ORIGINS: str = "http://localhost,http://localhost:80"  # noqa: S106

    # ── Superadmin ────────────────────────────────────────────────
    SUPERADMIN_EMAIL: str = "admin@example.com"
    SUPERADMIN_PASSWORD: str = "admin"

    # ── LLM ───────────────────────────────────────────────────────
    LLM_PROVIDER: Literal["gigachat", "yandex", "openrouter", "vsegpt"] = "openrouter"

    GIGACHAT_CREDENTIALS: str = ""
    GIGACHAT_SCOPE: str = "GIGACHAT_API_PERS"

    YANDEX_API_KEY: str = ""
    YANDEX_FOLDER_ID: str = ""

    OPENROUTER_API_KEY: str = ""
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"

    VSEGPT_API_KEY: str = ""
    VSEGPT_BASE_URL: str = "https://api.vsegpt.ru/v1"

    # ── SMTP ──────────────────────────────────────────────────────
    SMTP_HOST: str = "mailhog"
    SMTP_PORT: int = 1025
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "noreply@example.com"

    @model_validator(mode="after")
    def build_connection_urls(self) -> "Settings":
        """Construct DATABASE_URL, REDIS_URL, QDRANT_URL from parts when not set."""
        if not self.DATABASE_URL:
            self.DATABASE_URL = (
                f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
                f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
            )

        if not self.REDIS_URL:
            if self.REDIS_PASSWORD:
                self.REDIS_URL = (
                    f"redis://:{self.REDIS_PASSWORD}"
                    f"@{self.REDIS_HOST}:{self.REDIS_PORT}"
                )
            else:
                self.REDIS_URL = f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}"

        if not self.QDRANT_URL:
            self.QDRANT_URL = f"http://{self.QDRANT_HOST}:{self.QDRANT_PORT}"

        return self

    @property
    def allowed_origins_list(self) -> list[str]:
        """Return ALLOWED_ORIGINS as a list, parsed from comma-separated string."""
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]


settings = Settings()
