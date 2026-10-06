"""
Configuration management for the AI Coding Mentor application.
Uses Pydantic settings for type-safe environment variable handling.
"""

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings

# The project keeps its .env at the repository root, while the backend runs
# with backend/ as the working directory. Resolve both explicitly; the root
# file takes precedence when both exist.
_BACKEND_DIR = Path(__file__).resolve().parent.parent
_REPO_ROOT = _BACKEND_DIR.parent
_ENV_FILES = (
    str(_BACKEND_DIR / ".env"),
    str(_REPO_ROOT / ".env"),
)


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    debug: bool = Field(default=False, description="Enable debug mode")
    log_level: str = Field(default="INFO", description="Logging level")

    # CORS
    # Stored as a comma-separated string so the documented .env form
    # (`CORS_ORIGINS=a,b`) works without JSON escaping. Use the
    # `cors_origins_list` property wherever a list is needed.
    cors_origins: str = Field(
        default="http://localhost:3000,http://localhost:5173",
        description="Comma-separated allowed CORS origins for the frontend",
    )

    @property
    def cors_origins_list(self) -> list[str]:
        """Allowed origins as a list."""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

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

    # Persistence / privacy (Q10 defaults)
    store_code_text: bool = Field(
        default=True,
        description="Store redacted code text at checkpoints; false = diagnostics and metadata only",
    )
    retention_days: int | None = Field(
        default=None, description="Auto-purge records older than N days; None = keep until deletion"
    )

    # Adaptation (PH6)
    adaptation_enabled: bool = Field(
        default=True, description="Enable rule-based hint adaptation from the mistake record"
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
        env_file = _ENV_FILES
        env_file_encoding = "utf-8"
        case_sensitive = False
        # The shared .env is a documented superset: it also holds variables for
        # the sandbox runner and other tooling. Unknown keys must not stop the
        # API from starting.
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
