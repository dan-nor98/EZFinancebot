from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://finance:finance@localhost:5432/finance"
    core_api_key: str = Field(default="development-only-key", min_length=8)
    telegram_bot_token: str = ""
    telegram_webhook_secret: str = Field(default="development-secret", min_length=8)
    redis_url: str = "redis://localhost:6379/0"
    environment: str = "development"
    max_request_bytes: int = 16_384

    @field_validator("database_url")
    @classmethod
    def require_database(cls, value: str) -> str:
        if not (value.startswith("postgresql+") or value.startswith("sqlite+")):
            raise ValueError("DATABASE_URL must use PostgreSQL (SQLite is test-only)")
        if value.startswith("sqlite+") and not value.startswith("sqlite+pysqlite:///:memory:"):
            raise ValueError("SQLite is allowed only as an explicit in-memory test database")
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
