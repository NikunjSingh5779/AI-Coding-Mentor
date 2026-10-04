"""
AI Provider Configuration for AI Real-Time Coding Screener
Supports multiple AI providers: OpenRouter, NVIDIA NIM, Groq, Google, OpenAI, Local
"""

from functools import lru_cache
from typing import Literal

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class AIProviderConfig(BaseModel):
    """Base configuration for AI providers"""

    provider_type: str
    api_key: str = ""
    base_url: str
    model: str
    max_tokens: int = 2048
    temperature: float = 0.7
    timeout: int = 30
    extra_headers: dict[str, str] = Field(default_factory=dict)


class OpenRouterConfig(AIProviderConfig):
    """OpenRouter configuration"""

    provider_type: str = "openrouter"
    base_url: str = "https://openrouter.ai/api/v1"
    model: str = "anthropic/claude-3.5-sonnet"
    app_name: str = "AI-Coding-Screener"
    app_url: str = "https://github.com/your-repo/ai-coding-screener"

    def get_headers(self) -> dict[str, str]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": self.app_url,
            "X-Title": self.app_name,
        }
        headers.update(self.extra_headers)
        return headers


class NvidiaConfig(AIProviderConfig):
    """NVIDIA NIM configuration"""

    provider_type: str = "nvidia_nim"
    base_url: str = "https://integrate.api.nvidia.com/v1"
    model: str = "meta/codellama-70b-instruct"

    def get_headers(self) -> dict[str, str]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "accept": "application/json",
        }
        headers.update(self.extra_headers)
        return headers


class GroqConfig(AIProviderConfig):
    """Groq configuration"""

    provider_type: str = "groq"
    base_url: str = "https://api.groq.com/openai/v1"
    model: str = "llama3-70b-8192"
    max_tokens: int = 8192  # Groq supports higher token counts

    def get_headers(self) -> dict[str, str]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
        }
        headers.update(self.extra_headers)
        return headers


class GoogleConfig(AIProviderConfig):
    """Google AI configuration"""

    provider_type: str = "google"
    base_url: str = "https://generativelanguage.googleapis.com/v1beta"
    model: str = "gemini-1.5-pro"

    def get_headers(self) -> dict[str, str]:
        headers = {
            "x-goog-api-key": self.api_key,
        }
        headers.update(self.extra_headers)
        return headers


class OpenAIConfig(AIProviderConfig):
    """OpenAI configuration"""

    provider_type: str = "openai"
    base_url: str = "https://api.openai.com/v1"
    model: str = "gpt-4"

    def get_headers(self) -> dict[str, str]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
        }
        headers.update(self.extra_headers)
        return headers


class LocalConfig(AIProviderConfig):
    """Local LLM configuration (LM Studio, Ollama, etc.)"""

    provider_type: str = "local"
    base_url: str = "http://localhost:1234/v1"
    model: str = "codellama"
    api_key: str = ""  # Usually not required for local

    def get_headers(self) -> dict[str, str]:
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        headers.update(self.extra_headers)
        return headers


class AISettings(BaseSettings):
    """AI provider settings with multi-provider support"""

    # Primary provider selection
    ai_provider: Literal[
        "openrouter", "nvidia_nim", "groq", "google", "openai", "local"
    ] = "local"

    # Provider-specific configurations
    openrouter_api_key: str = ""
    openrouter_model: str = "anthropic/claude-3.5-sonnet"
    openrouter_app_name: str = "AI-Coding-Screener"
    openrouter_app_url: str = "https://github.com/your-repo/ai-coding-screener"

    nvidia_nim_api_key: str = ""
    nvidia_nim_model: str = "meta/codellama-70b-instruct"

    groq_api_key: str = ""
    groq_model: str = "llama3-70b-8192"

    google_api_key: str = ""
    google_model: str = "gemini-1.5-pro"

    openai_api_key: str = ""
    openai_model: str = "gpt-4"

    local_base_url: str = "http://localhost:1234/v1"
    local_model: str = "codellama"

    # Global AI settings
    ai_temperature: float = 0.7
    ai_max_tokens: int = 2048
    ai_timeout: int = 30

    # Fallback configuration
    enable_fallback: bool = True
    fallback_providers: list[str] = Field(default_factory=lambda: ["local", "openai"])

    class Config:
        env_file = ".env"
        case_sensitive = False
        env_prefix = ""  # Allow both prefixed and non-prefixed env vars


def get_provider_config(
    settings: AISettings, provider: str | None = None
) -> AIProviderConfig:
    """Get configuration for the specified provider or current primary provider"""
    provider_name = provider or settings.ai_provider

    config_map = {
        "openrouter": OpenRouterConfig(
            api_key=settings.openrouter_api_key,
            model=settings.openrouter_model,
            app_name=settings.openrouter_app_name,
            app_url=settings.openrouter_app_url,
            temperature=settings.ai_temperature,
            max_tokens=settings.ai_max_tokens,
            timeout=settings.ai_timeout,
        ),
        "nvidia_nim": NvidiaConfig(
            api_key=settings.nvidia_nim_api_key,
            model=settings.nvidia_nim_model,
            temperature=settings.ai_temperature,
            max_tokens=settings.ai_max_tokens,
            timeout=settings.ai_timeout,
        ),
        "groq": GroqConfig(
            api_key=settings.groq_api_key,
            model=settings.groq_model,
            temperature=settings.ai_temperature,
            max_tokens=min(settings.ai_max_tokens, 8192),  # Groq limit
            timeout=settings.ai_timeout,
        ),
        "google": GoogleConfig(
            api_key=settings.google_api_key,
            model=settings.google_model,
            temperature=settings.ai_temperature,
            max_tokens=settings.ai_max_tokens,
            timeout=settings.ai_timeout,
        ),
        "openai": OpenAIConfig(
            api_key=settings.openai_api_key,
            model=settings.openai_model,
            temperature=settings.ai_temperature,
            max_tokens=settings.ai_max_tokens,
            timeout=settings.ai_timeout,
        ),
        "local": LocalConfig(
            base_url=settings.local_base_url,
            model=settings.local_model,
            temperature=settings.ai_temperature,
            max_tokens=settings.ai_max_tokens,
            timeout=settings.ai_timeout,
        ),
    }

    if provider_name not in config_map:
        raise ValueError(f"Unknown AI provider: {provider_name}")

    return config_map[provider_name]


@lru_cache
def get_ai_settings() -> AISettings:
    """Get cached AI settings instance"""
    return AISettings()


def get_available_providers(settings: AISettings) -> list[str]:
    """Get list of available providers (those with API keys configured)"""
    available = []

    # Check each provider for required configuration
    if settings.openrouter_api_key:
        available.append("openrouter")

    if settings.nvidia_nim_api_key:
        available.append("nvidia_nim")

    if settings.groq_api_key:
        available.append("groq")

    if settings.google_api_key:
        available.append("google")

    if settings.openai_api_key:
        available.append("openai")

    # Local is always available (doesn't require API key)
    available.append("local")

    return available


def validate_provider_config(config: AIProviderConfig) -> bool:
    """Validate that a provider configuration is complete and usable"""
    if not config.base_url:
        return False

    if not config.model:
        return False

    # Check API key requirement (not needed for local)
    if config.provider_type != "local" and not config.api_key:
        return False

    return True
