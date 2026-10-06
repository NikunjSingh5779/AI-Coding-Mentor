"""Application configuration for the AI Coding Mentor."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Single source of truth for runtime configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "AI Coding Mentor"
    app_env: str = "development"
    debug: bool = False
    log_level: str = "INFO"

    cors_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ]
    )

    # Database. SQLite is the zero-configuration local default; PostgreSQL is
    # supported by setting DATABASE_URL in production/Compose.
    database_url: str = "sqlite+aiosqlite:///./mentor.db"
    store_code_text: bool = False
    retention_days: int = 30

    # Analysis
    enabled_analyzers: list[str] = Field(
        default_factory=lambda: ["python_ast", "treesitter", "ruff"]
    )
    enabled_languages: list[str] = Field(
        default_factory=lambda: ["python", "javascript", "cpp", "java", "c"]
    )
    max_code_bytes: int = 250_000
    max_message_bytes: int = 1_048_576

    # Execution / sandbox
    execution_enabled: bool = True
    sandbox_url: str = "http://localhost:8100"
    sandbox_secret: str = "change-me-sandbox-secret"
    sandbox_timeout: int = 30
    sandbox_max_timeout: int = 60
    sandbox_max_output_bytes: int = 1_048_576
    max_concurrent_runs: int = 3

    # Mentor / LLM
    llm_enabled: bool = True
    llm_provider: str = "openai_compatible"
    llm_base_url: str = "http://127.0.0.1:8080/v1"
    llm_api_key: str = "none"
    llm_model: str = "auto"
    llm_timeout: float = 30.0
    llm_max_tokens: int = 320
    llm_temperature: float = 0.2
    mentor_max_hints_per_session: int = 20
    mentor_max_hint_chars: int = 900
    adaptive_enabled: bool = True
    max_requests_per_minute: int = 120

    # Screen source / OCR
    feature_screen_source: bool = False
    auto_code_discovery_enabled: bool = True
    ocr_engine: str = "tesseract"
    region_confidence_gate: float = 0.55
    max_frame_bytes: int = 2 * 1024 * 1024
    screen_sample_interval_ms: int = 1500

    # WebSocket
    ws_heartbeat_interval: int = 30

    # UI
    floating_mentor_enabled: bool = True

    # Security
    secret_key: str = "change-me-in-production"


@lru_cache
def get_settings() -> Settings:
    """Return the cached settings singleton."""

    return Settings()
