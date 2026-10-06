"""
Configuration management for the AI Coding Mentor application.
Uses Pydantic settings for type-safe environment variable handling.
"""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    debug: bool = Field(default=False, description="Enable debug mode")
    log_level: str = Field(default="INFO", description="Logging level")

    # CORS
    cors_origins: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173"],
        description="Allowed CORS origins for frontend",
    )

    # Features
    feature_screen_source: bool = Field(
        default=False, description="Enable screen capture and OCR analysis"
    )

    # Database (for later phases)
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/coding_mentor",
        description="Database connection URL",
    )

    # Sandbox runner
    execution_enabled: bool = Field(
        default=True, description="Enable code execution in the sandbox runner"
    )
    sandbox_url: str = Field(
        default="http://localhost:8100", description="Sandbox runner service URL"
    )
    sandbox_secret: str = Field(
        default="mentor-sandbox-secret-dev", description="Shared secret for sandbox runner authentication"
    )
    sandbox_timeout: int = Field(
        default=10, description="Sandbox execution timeout in seconds"
    )

    # LLM settings (for later phases)
    llm_enabled: bool = Field(
        default=False, description="Enable LLM-backed hints; false = template fallbacks only"
    )
    llm_provider: str = Field(
        default="openai_compatible", description="LLM provider to use"
    )
    llm_base_url: str = Field(
        default="http://localhost:1234/v1", description="Base URL for LLM API"
    )
    llm_api_key: str = Field(default="lm-studio", description="API key for LLM service")
    llm_model: str = Field(
        default="qwen2.5-coder-14b-instruct", description="Model name to use"
    )

    # Rate limiting
    max_requests_per_minute: int = Field(
        default=60, description="Maximum requests per minute per session"
    )
    max_concurrent_runs: int = Field(
        default=3, description="Maximum concurrent code executions"
    )

    # Mentor settings
    mentor_proactivity_default: str = Field(
        default="balanced", description="Default mentor proactivity (quiet|balanced|proactive)"
    )
    hint_cooldown_seconds: int = Field(
        default=20, description="Minimum seconds between mentor messages per issue"
    )
    hosted_llm_budget_session: int = Field(
        default=50, description="Max hosted LLM hint generations per session"
    )
    hosted_llm_budget_day: int = Field(
        default=200, description="Max hosted LLM hint generations per day"
    )

    # WebSocket
    ws_heartbeat_interval: int = Field(
        default=30, description="WebSocket heartbeat interval in seconds"
    )
    ws_max_message_size: int = Field(
        default=1024 * 1024,  # 1MB
        description="Maximum WebSocket message size in bytes",
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
