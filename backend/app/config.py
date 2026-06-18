"""Application configuration via pydantic-settings.

Loads every key from the repository ``.env.example`` contract. Secrets stay out
of source — values come from the environment / ``.env`` file. A computed
``DEMO_MODE`` flag (true in development) drives the graceful-degradation
fallbacks used across the API when the database or cache is empty/unreachable.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Strongly-typed settings mirroring ``.env.example``."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ────────────────────────────────────────────────────────
    APP_NAME: str = "Venezuela Political Intelligence Dashboard"
    APP_ENV: str = "development"  # development | staging | production
    APP_DEBUG: bool = True
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    APP_TIMEZONE: str = "America/Caracas"
    APP_DEFAULT_LOCALE: str = "es"
    FRONTEND_ORIGIN: str = "http://localhost:5173"

    # ── Database (PostgreSQL) ──────────────────────────────────────────────
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "vpid"
    POSTGRES_USER: str = "vpid_app"
    POSTGRES_PASSWORD: str = "change_me_strong_password"
    DATABASE_URL: str = (
        "postgresql+asyncpg://vpid_app:change_me_strong_password@localhost:5432/vpid"
    )

    # ── Supabase (optional / server-side only) ─────────────────────────────
    SUPABASE_URL: str = ""
    SUPABASE_ANON_KEY: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""

    # ── Security / Auth ────────────────────────────────────────────────────
    JWT_SECRET_KEY: str = "generate_a_64_char_random_secret"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    PASSWORD_HASH_SCHEME: str = "bcrypt"

    # ── Cache (Redis) ──────────────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"
    CACHE_TTL_SECONDS: int = 300

    # ── AI / NLP providers ─────────────────────────────────────────────────
    AI_PROVIDER: str = "local"  # local | anthropic | openai
    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MODEL: str = "claude-opus-4-8"
    AI_SENTIMENT_BATCH_SIZE: int = 25

    # ── ETL / ingestion ────────────────────────────────────────────────────
    ETL_SCHEDULE_CRON: str = "0 5 * * *"
    ETL_USER_AGENT: str = "VPID-OSINT-Bot/1.0 (+public-sources-only)"
    ETL_REQUEST_TIMEOUT: int = 20
    ETL_MAX_ARTICLES_PER_SOURCE: int = 200
    ETL_RESPECT_ROBOTS_TXT: bool = True

    # ── Reports (PDF) ──────────────────────────────────────────────────────
    REPORTS_STORAGE_PATH: str = "./storage/reports"
    REPORT_DAILY_CRON: str = "0 6 * * *"
    REPORT_BRAND_NAME: str = "Venezuela Political Intelligence"
    REPORT_LOGO_PATH: str = "./frontend/assets/img/logo.svg"

    # ── App metadata (not in .env; sensible defaults) ──────────────────────
    API_V1_PREFIX: str = "/api/v1"
    VERSION: str = "1.0.0"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def DEMO_MODE(self) -> bool:
        """Demo fallbacks are on outside production.

        Used as a safety net so the API is always demoable: read endpoints fall
        back to representative in-memory data when the DB is empty/unreachable.
        """
        return self.APP_ENV.lower() != "production"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def cors_origins(self) -> list[str]:
        """CORS allow-list derived from ``FRONTEND_ORIGIN`` (comma-separated)."""
        return [o.strip() for o in self.FRONTEND_ORIGIN.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    """Return a cached ``Settings`` instance (one read of the environment)."""
    return Settings()


# Module-level singleton for convenient imports.
settings = get_settings()
