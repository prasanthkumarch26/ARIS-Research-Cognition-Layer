from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import PostgresDsn, RedisDsn, AnyUrl, Field
from typing import Literal
from functools import lru_cache

class Settings(BaseSettings):
    # Settings configuration
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        env_prefix="APP_",
        frozen=True,
    )

    # Application metadata
    app_name: str = "Research Paper Intelligence System"
    app_version: str = "1.0.0"
    env: Literal["development", "production", "testing"] = "development"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"

    # Server configuration
    host: str = "0.0.0.0"
    port: int = Field(8000, ge=1024, le=65535)
    max_concurrent_requests: int = Field(200, ge=10, le=10000)

    # Database configuration
    database_url: PostgresDsn
    db_min_connections: int = Field(10, ge=5, le=100)
    db_max_connections: int = Field(30, ge=10, le=500)

    # Redis configuration
    redis_url: RedisDsn
    redis_ttl_search: int = Field(300, ge=3, le=3600)
    redis_ttl_paper: int = Field(3600, ge=3, le=86400)
    redis_timeout: int = Field(5, ge=1, le=60)
    redis_max_connections: int = Field(20, ge=10, le=500)

    # arXiv
    arxiv_api_url: AnyUrl = "https://export.arxiv.org/api/query"
    arxiv_retry_delay: float = Field(3.0, ge=3.0, le=60.0)
    arxiv_max_retries: int = Field(3, ge=3, le=10)
    arxiv_default_results: int = Field(100, ge=1, le=1000)

    @property
    def debug(self) -> bool:
        return self.env == "development"


@lru_cache
def get_settings():
    return Settings()

settings = get_settings()
