"""Application configuration loaded from environment variables."""
from __future__ import annotations

from functools import lru_cache
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings. All values come from env vars (or .env file)."""

    database_url: str = Field(
        default="postgresql+psycopg2://faceuser:facepass@localhost:5432/facedb",
        alias="DATABASE_URL",
    )
    allowed_origins: str = Field(
        default="http://localhost:5173,http://localhost:3000",
        alias="ALLOWED_ORIGINS",
    )
    # Hard ceiling on per-frame size to bound resource usage / DOS vector.
    max_frame_bytes: int = Field(default=2_000_000, alias="MAX_FRAME_BYTES")
    # Cap incoming frame rate per connection to prevent CPU/DoS abuse.
    max_ingest_fps: int = Field(default=30, alias="MAX_INGEST_FPS")

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origins(self) -> List[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
