"""Provider registry: choose the mentor LLM backend from application settings."""

from __future__ import annotations

from functools import lru_cache

from app.config import get_settings
from app.core.logging import get_logger

from .base import LLMProvider
from .openai_compatible import DisabledProvider, OpenAICompatibleProvider

logger = get_logger(__name__)


@lru_cache
def get_llm_provider() -> LLMProvider:
    """Build the singleton provider from settings (LLM_ENABLED / LLM_BASE_URL / ...)."""
    settings = get_settings()
    if not settings.llm_enabled:
        logger.info("LLM disabled; mentor will use template fallbacks only")
        return DisabledProvider()
    provider = OpenAICompatibleProvider(
        base_url=settings.llm_base_url,
        api_key=settings.llm_api_key,
        model=settings.llm_model,
    )
    logger.info(
        "LLM provider configured",
        extra={"base_url": settings.llm_base_url, "model": settings.llm_model},
    )
    return provider


def reset_llm_provider() -> None:
    """Clear the cached provider (used by tests)."""
    get_llm_provider.cache_clear()
