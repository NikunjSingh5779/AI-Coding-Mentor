"""
Configuration management for AI Real-Time Coding Screener
Following MVC pattern: Core layer handles application configuration
"""
from functools import lru_cache
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support"""

    # Application
    app_name: str = "AI Real-Time Coding Screener"
    debug: bool = False
    host: str = "127.0.0.1"
    port: int = 8000

    # Database
    database_url: str = "postgresql+asyncpg://user:pass@localhost/ai_screener"

    # CORS
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:5173"]

    # LLM Configuration
    llm_provider: str = "local"  # "local" or "hosted"
    llm_local_url: str = "http://localhost:1234/v1"
    llm_hosted_api_key: str = ""
    llm_model_name: str = "codellama"

    # Sandbox
    sandbox_timeout: int = 30
    sandbox_memory_limit: str = "512m"

    # Mentor Configuration
    hint_levels: int = 4
    max_hints_per_session: int = 10

    # Security
    secret_key: str = "your-secret-key-change-this"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # Logging
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()