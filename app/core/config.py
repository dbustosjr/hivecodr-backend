"""Application configuration settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Anthropic API
    ANTHROPIC_API_KEY: str
    CLAUDE_MODEL: str = "claude-sonnet-4-20250514"

    # Supabase
    SUPABASE_URL: str
    SUPABASE_KEY: str
    SUPABASE_JWT_SECRET: str

    # Application
    ENVIRONMENT: str = "development"
    MAX_DAILY_COST: float = 100.0
    RATE_LIMIT_GENERATIONS: int = 10
    RATE_LIMIT_WINDOW: int = 3600  # 1 hour in seconds
    MAX_INPUT_LENGTH: int = 5000

    # API Settings
    API_V1_PREFIX: str = "/api"
    PROJECT_NAME: str = "HiveCodr Backend"
    VERSION: str = "1.0.0"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )


# Global settings instance
settings = Settings()
