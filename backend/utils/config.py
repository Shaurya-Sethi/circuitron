from __future__ import annotations

from __future__ import annotations

from functools import lru_cache

from pydantic import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment."""

    openrouter_api_key: str | None = None

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


