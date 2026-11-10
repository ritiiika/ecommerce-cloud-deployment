"""Application configuration loaded from environment variables."""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://ecom:ecom_pass@db:5432/ecomdb"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20

    # API
    API_KEY_ADMIN: str = "changeme-admin-key"  # Override via env
    LOG_LEVEL: str = "INFO"
    CORS_ORIGINS: List[str] = ["*"]

    # App
    APP_ENV: str = "development"
    APP_VERSION: str = "1.0.0"


settings = Settings()
