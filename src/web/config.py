"""Centralized configuration via environment variables."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings, populated from environment variables (.env)."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_host: str = "0.0.0.0"
    app_port: int = 8000
    app_password: str = "change-me"
    app_secret_key: str = "change-me"

    database_url: str = "postgresql+asyncpg://pvsim:pvsim@postgres:5432/pvsim"
    redis_url: str = "redis://redis:6379/0"

    load_profiles_dir: str = "/data/load_profiles"


@lru_cache
def get_settings() -> Settings:
    return Settings()
