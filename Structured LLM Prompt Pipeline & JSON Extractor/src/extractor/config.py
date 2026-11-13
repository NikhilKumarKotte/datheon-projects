from functools import lru_cache
from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables or .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Gemini API Credentials
    gemini_api_key: str = Field(
        default="",
        alias="GEMINI_API_KEY",
        description="Google Gemini API key",
    )

    # Model Configuration
    default_model: str = Field(
        default="gemini-3.5-flash-lite",
        alias="DEFAULT_MODEL",
        description="Default Gemini model to use for extraction",
    )
    fallback_models: List[str] = Field(
        default=["gemini-3.8-flash", "gemini-flash-latest"],
        alias="FALLBACK_MODELS",
        description="List of fallback models if primary model is unavailable or rate-limited",
    )

    # Server Configuration
    server_host: str = Field(
        default="0.0.0.0",
        alias="HOST",
        description="API server binding host",
    )
    server_port: int = Field(
        default=8000,
        alias="PORT",
        description="API server binding port",
    )
    cors_origins: List[str] = Field(
        default=["*"],
        alias="CORS_ORIGINS",
        description="Allowed CORS origins",
    )

    # Operational Settings
    max_retries: int = Field(
        default=2,
        alias="MAX_RETRIES",
        description="Maximum retry attempts on transient model failures",
    )
    timeout_seconds: float = Field(
        default=45.0,
        alias="TIMEOUT_SECONDS",
        description="HTTP request timeout for LLM client",
    )
    environment: str = Field(
        default="development",
        alias="ENVIRONMENT",
        description="Deployment environment (development, staging, production)",
    )
    log_level: str = Field(
        default="INFO",
        alias="LOG_LEVEL",
        description="Logging level",
    )


@lru_cache()
def get_settings() -> Settings:
    """Return cached application settings singleton."""
    return Settings()
