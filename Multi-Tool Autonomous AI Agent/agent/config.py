"""Configuration module for the Autonomous Multi-Tool AI Agent.

Loads environment variables via python-dotenv and provides strongly-typed
settings using Pydantic.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Literal, Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

# Search for .env in current directory and parent directories
load_dotenv()


class Settings(BaseSettings):
    """Application configuration and environment settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # LLM Settings
    llm_provider: Literal["openai", "google", "ollama", "mock"] = Field(
        default="openai",
        alias="LLM_PROVIDER",
        description="LLM Provider to use ('openai', 'google', 'ollama', 'mock')",
    )
    llm_model: str = Field(
        default="gpt-4o-mini",
        alias="LLM_MODEL",
        description="Model name/id to instantiate",
    )
    llm_temperature: float = Field(
        default=0.0,
        alias="LLM_TEMPERATURE",
        description="Sampling temperature for deterministic tool invocation",
    )

    # API Keys
    openai_api_key: Optional[str] = Field(
        default=None,
        alias="OPENAI_API_KEY",
        description="OpenAI API key",
    )
    google_api_key: Optional[str] = Field(
        default=None,
        alias="GOOGLE_API_KEY",
        description="Google Gemini API key",
    )
    tavily_api_key: Optional[str] = Field(
        default=None,
        alias="TAVILY_API_KEY",
        description="Optional Tavily API key for search fallback",
    )

    # Ollama / Local LLM settings
    ollama_base_url: str = Field(
        default="http://localhost:11434",
        alias="OLLAMA_BASE_URL",
        description="Base URL for local Ollama instance",
    )
    ollama_model: str = Field(
        default="llama3.2",
        alias="OLLAMA_MODEL",
        description="Ollama model tag to pull/use",
    )

    # File Reader Sandbox
    file_reader_base_dir: Path = Field(
        default_factory=lambda: Path.cwd(),
        alias="FILE_READER_BASE_DIR",
        description="Base directory for sandboxing local file reader",
    )
    max_file_read_bytes: int = Field(
        default=1_048_576,  # 1 MB
        alias="MAX_FILE_READ_BYTES",
        description="Maximum file size in bytes to read into memory",
    )

    # Agent Loop Controls
    max_iterations: int = Field(
        default=10,
        alias="MAX_ITERATIONS",
        description="Maximum autonomous tool-execution steps before stopping",
    )
    verbose_output: bool = Field(
        default=True,
        alias="VERBOSE_OUTPUT",
        description="Whether to show full formatted reasoning chain logs",
    )


# Instantiate singleton settings
settings = Settings()
