"""Application configuration loaded from environment variables."""

from __future__ import annotations

import os

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"), env_file_encoding="utf-8", extra="ignore"
    )

    app_name: str = "RiskLens API"
    environment: str = "development"

    # Database. Prefer DATABASE_URL (Neon Postgres). Falls back to local SQLite.
    database_url: str = os.getenv(
        "DATABASE_URL", "sqlite:///./risklens.db"
    )

    # Auth
    secret_key: str = os.getenv("SECRET_KEY", "dev-insecure-change-me")
    access_token_expire_minutes: int = 60 * 24
    algorithm: str = "HS256"

    # CORS
    cors_origins: str = os.getenv("CORS_ORIGINS", "http://localhost:3000")

    # Optional LLM key for news summarisation (graceful fallback if absent)
    llm_api_key: str | None = os.getenv("LLM_API_KEY")

    @property
    def sqlalchemy_url(self) -> str:
        url = self.database_url
        # normalise Neon/psql style URLs to the psycopg3 driver
        if url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+psycopg://", 1)
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+psycopg://", 1)
        return url

    @property
    def cors_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
