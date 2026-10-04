"""
AI Client Implementation for Multiple Providers
Supports OpenRouter, NVIDIA NIM, Groq, Google AI, OpenAI, and Local LLMs
"""

import json
import logging
from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from typing import Any

import httpx

from .ai_config import (
    AIProviderConfig,
    GoogleConfig,
    GroqConfig,
    LocalConfig,
    NvidiaConfig,
    OpenAIConfig,
    OpenRouterConfig,
    get_ai_settings,
    get_available_providers,
    get_provider_config,
    validate_provider_config,
)

logger = logging.getLogger(__name__)


class AIProviderError(Exception):
    """Base exception for AI provider errors"""

    def __init__(self, message: str, provider: str, status_code: int | None = None):
        super().__init__(message)
        self.provider = provider
        self.status_code = status_code


class AIProvider(ABC):
    """Abstract base class for AI providers"""

    def __init__(self, config: AIProviderConfig):
        self.config = config
        self.client = httpx.AsyncClient(
            timeout=config.timeout,
            headers=config.get_headers() if hasattr(config, "get_headers") else {},
        )

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    @abstractmethod
    async def generate_completion(
        self, messages: list[dict[str, str]], **kwargs
    ) -> str:
        """Generate a completion from messages"""
        pass

    @abstractmethod
    async def stream_completion(
        self, messages: list[dict[str, str]], **kwargs
    ) -> AsyncGenerator[str, None]:
        """Stream a completion from messages"""
        pass

    def format_messages(self, messages: list[dict[str, str]]) -> list[dict[str, str]]:
        """Format messages for the provider (override if needed)"""
        return messages


class OpenRouterProvider(AIProvider):
    """OpenRouter AI provider implementation"""

    def __init__(self, config: OpenRouterConfig):
        super().__init__(config)
        self.client.headers.update(
            {
                "HTTP-Referer": config.app_url,
                "X-Title": config.app_name,
            }
        )

    async def generate_completion(
        self, messages: list[dict[str, str]], **kwargs
    ) -> str:
        try:
            response = await self.client.post(
                f"{self.config.base_url}/chat/completions",
                json={
                    "model": self.config.model,
                    "messages": self.format_messages(messages),
                    "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
                    "temperature": kwargs.get("temperature", self.config.temperature),
                    "stream": False,
                },
            )
            response.raise_for_status()

            result = response.json()
            return result["choices"][0]["message"]["content"]

        except httpx.HTTPError as e:
            raise AIProviderError(
                f"OpenRouter API error: {str(e)}",
                "openrouter",
                getattr(e.response, "status_code", None),
            )

    async def stream_completion(
        self, messages: list[dict[str, str]], **kwargs
    ) -> AsyncGenerator[str, None]:
        try:
            async with self.client.stream(
                "POST",
                f"{self.config.base_url}/chat/completions",
                json={
                    "model": self.config.model,
                    "messages": self.format_messages(messages),
                    "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
                    "temperature": kwargs.get("temperature", self.config.temperature),
                    "stream": True,
                },
            ) as response:
                response.raise_for_status()

                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        if data == "[DONE]":
                            break

                        try:
                            chunk = json.loads(data)
                            if chunk["choices"][0]["delta"].get("content"):
                                yield chunk["choices"][0]["delta"]["content"]
                        except (json.JSONDecodeError, KeyError):
                            continue

        except httpx.HTTPError as e:
            raise AIProviderError(f"OpenRouter streaming error: {str(e)}", "openrouter")


class NvidiaProvider(AIProvider):
    """NVIDIA NIM provider implementation"""

    async def generate_completion(
        self, messages: list[dict[str, str]], **kwargs
    ) -> str:
        try:
            response = await self.client.post(
                f"{self.config.base_url}/chat/completions",
                json={
                    "model": self.config.model,
                    "messages": self.format_messages(messages),
                    "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
                    "temperature": kwargs.get("temperature", self.config.temperature),
                    "stream": False,
                },
            )
            response.raise_for_status()

            result = response.json()
            return result["choices"][0]["message"]["content"]

        except httpx.HTTPError as e:
            raise AIProviderError(
                f"NVIDIA NIM API error: {str(e)}",
                "nvidia_nim",
                getattr(e.response, "status_code", None),
            )

    async def stream_completion(
        self, messages: list[dict[str, str]], **kwargs
    ) -> AsyncGenerator[str, None]:
        # Implementation similar to OpenRouter
        try:
            async with self.client.stream(
                "POST",
                f"{self.config.base_url}/chat/completions",
                json={
                    "model": self.config.model,
                    "messages": self.format_messages(messages),
                    "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
                    "temperature": kwargs.get("temperature", self.config.temperature),
                    "stream": True,
                },
            ) as response:
                response.raise_for_status()

                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        if data == "[DONE]":
                            break

                        try:
                            chunk = json.loads(data)
                            if chunk["choices"][0]["delta"].get("content"):
                                yield chunk["choices"][0]["delta"]["content"]
                        except (json.JSONDecodeError, KeyError):
                            continue

        except httpx.HTTPError as e:
            raise AIProviderError(f"NVIDIA NIM streaming error: {str(e)}", "nvidia_nim")


class GroqProvider(AIProvider):
    """Groq provider implementation"""

    async def generate_completion(
        self, messages: list[dict[str, str]], **kwargs
    ) -> str:
        try:
            response = await self.client.post(
                f"{self.config.base_url}/chat/completions",
                json={
                    "model": self.config.model,
                    "messages": self.format_messages(messages),
                    "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
                    "temperature": kwargs.get("temperature", self.config.temperature),
                },
            )
            response.raise_for_status()

            result = response.json()
            return result["choices"][0]["message"]["content"]

        except httpx.HTTPError as e:
            raise AIProviderError(
                f"Groq API error: {str(e)}",
                "groq",
                getattr(e.response, "status_code", None),
            )

    async def stream_completion(
        self, messages: list[dict[str, str]], **kwargs
    ) -> AsyncGenerator[str, None]:
        # Similar streaming implementation
        try:
            async with self.client.stream(
                "POST",
                f"{self.config.base_url}/chat/completions",
                json={
                    "model": self.config.model,
                    "messages": self.format_messages(messages),
                    "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
                    "temperature": kwargs.get("temperature", self.config.temperature),
                    "stream": True,
                },
            ) as response:
                response.raise_for_status()

                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        if data == "[DONE]":
                            break

                        try:
                            chunk = json.loads(data)
                            if chunk["choices"][0]["delta"].get("content"):
                                yield chunk["choices"][0]["delta"]["content"]
                        except (json.JSONDecodeError, KeyError):
                            continue

        except httpx.HTTPError as e:
            raise AIProviderError(f"Groq streaming error: {str(e)}", "groq")


class GoogleProvider(AIProvider):
    """Google AI provider implementation"""

    def format_messages(self, messages: list[dict[str, str]]) -> dict[str, Any]:
        """Google AI uses a different message format"""
        contents = []
        for msg in messages:
            role = "user" if msg["role"] == "user" else "model"
            contents.append({"role": role, "parts": [{"text": msg["content"]}]})
        return {"contents": contents}

    async def generate_completion(
        self, messages: list[dict[str, str]], **kwargs
    ) -> str:
        try:
            formatted_data = self.format_messages(messages)
            formatted_data.update(
                {
                    "generationConfig": {
                        "maxOutputTokens": kwargs.get(
                            "max_tokens", self.config.max_tokens
                        ),
                        "temperature": kwargs.get(
                            "temperature", self.config.temperature
                        ),
                    }
                }
            )

            response = await self.client.post(
                f"{self.config.base_url}/models/{self.config.model}:generateContent",
                json=formatted_data,
            )
            response.raise_for_status()

            result = response.json()
            return result["candidates"][0]["content"]["parts"][0]["text"]

        except httpx.HTTPError as e:
            raise AIProviderError(
                f"Google AI API error: {str(e)}",
                "google",
                getattr(e.response, "status_code", None),
            )

    async def stream_completion(
        self, messages: list[dict[str, str]], **kwargs
    ) -> AsyncGenerator[str, None]:
        # Google AI streaming implementation
        try:
            formatted_data = self.format_messages(messages)
            formatted_data.update(
                {
                    "generationConfig": {
                        "maxOutputTokens": kwargs.get(
                            "max_tokens", self.config.max_tokens
                        ),
                        "temperature": kwargs.get(
                            "temperature", self.config.temperature
                        ),
                    }
                }
            )

            async with self.client.stream(
                "POST",
                f"{self.config.base_url}/models/{self.config.model}:streamGenerateContent",
                json=formatted_data,
            ) as response:
                response.raise_for_status()

                async for line in response.aiter_lines():
                    try:
                        chunk = json.loads(line)
                        if "candidates" in chunk and chunk["candidates"]:
                            candidate = chunk["candidates"][0]
                            if (
                                "content" in candidate
                                and "parts" in candidate["content"]
                            ):
                                for part in candidate["content"]["parts"]:
                                    if "text" in part:
                                        yield part["text"]
                    except (json.JSONDecodeError, KeyError):
                        continue

        except httpx.HTTPError as e:
            raise AIProviderError(f"Google AI streaming error: {str(e)}", "google")


class OpenAIProvider(AIProvider):
    """OpenAI provider implementation (fallback/reference)"""

    async def generate_completion(
        self, messages: list[dict[str, str]], **kwargs
    ) -> str:
        try:
            response = await self.client.post(
                f"{self.config.base_url}/chat/completions",
                json={
                    "model": self.config.model,
                    "messages": self.format_messages(messages),
                    "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
                    "temperature": kwargs.get("temperature", self.config.temperature),
                },
            )
            response.raise_for_status()

            result = response.json()
            return result["choices"][0]["message"]["content"]

        except httpx.HTTPError as e:
            raise AIProviderError(
                f"OpenAI API error: {str(e)}",
                "openai",
                getattr(e.response, "status_code", None),
            )

    async def stream_completion(
        self, messages: list[dict[str, str]], **kwargs
    ) -> AsyncGenerator[str, None]:
        # Standard OpenAI streaming implementation
        try:
            async with self.client.stream(
                "POST",
                f"{self.config.base_url}/chat/completions",
                json={
                    "model": self.config.model,
                    "messages": self.format_messages(messages),
                    "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
                    "temperature": kwargs.get("temperature", self.config.temperature),
                    "stream": True,
                },
            ) as response:
                response.raise_for_status()

                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        if data == "[DONE]":
                            break

                        try:
                            chunk = json.loads(data)
                            if chunk["choices"][0]["delta"].get("content"):
                                yield chunk["choices"][0]["delta"]["content"]
                        except (json.JSONDecodeError, KeyError):
                            continue

        except httpx.HTTPError as e:
            raise AIProviderError(f"OpenAI streaming error: {str(e)}", "openai")


class LocalProvider(AIProvider):
    """Local LLM provider (LM Studio, Ollama, etc.)"""

    async def generate_completion(
        self, messages: list[dict[str, str]], **kwargs
    ) -> str:
        try:
            response = await self.client.post(
                f"{self.config.base_url}/chat/completions",
                json={
                    "model": self.config.model,
                    "messages": self.format_messages(messages),
                    "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
                    "temperature": kwargs.get("temperature", self.config.temperature),
                },
            )
            response.raise_for_status()

            result = response.json()
            return result["choices"][0]["message"]["content"]

        except httpx.HTTPError as e:
            raise AIProviderError(
                f"Local LLM error: {str(e)}",
                "local",
                getattr(e.response, "status_code", None),
            )

    async def stream_completion(
        self, messages: list[dict[str, str]], **kwargs
    ) -> AsyncGenerator[str, None]:
        try:
            async with self.client.stream(
                "POST",
                f"{self.config.base_url}/chat/completions",
                json={
                    "model": self.config.model,
                    "messages": self.format_messages(messages),
                    "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
                    "temperature": kwargs.get("temperature", self.config.temperature),
                    "stream": True,
                },
            ) as response:
                response.raise_for_status()

                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        if data == "[DONE]":
                            break

                        try:
                            chunk = json.loads(data)
                            if chunk["choices"][0]["delta"].get("content"):
                                yield chunk["choices"][0]["delta"]["content"]
                        except (json.JSONDecodeError, KeyError):
                            continue

        except httpx.HTTPError as e:
            raise AIProviderError(f"Local LLM streaming error: {str(e)}", "local")


# Provider factory
PROVIDER_MAP = {
    "openrouter": (OpenRouterProvider, OpenRouterConfig),
    "nvidia_nim": (NvidiaProvider, NvidiaConfig),
    "groq": (GroqProvider, GroqConfig),
    "google": (GoogleProvider, GoogleConfig),
    "openai": (OpenAIProvider, OpenAIConfig),
    "local": (LocalProvider, LocalConfig),
}


def create_ai_provider(provider_name: str | None = None) -> AIProvider:
    """Factory function to create AI provider instances"""
    settings = get_ai_settings()
    provider_name = provider_name or settings.ai_provider

    if provider_name not in PROVIDER_MAP:
        raise ValueError(f"Unknown AI provider: {provider_name}")

    provider_class, config_class = PROVIDER_MAP[provider_name]
    config = get_provider_config(settings, provider_name)

    if not validate_provider_config(config):
        raise AIProviderError(
            f"Invalid configuration for provider: {provider_name}", provider_name
        )

    return provider_class(config)


class AIManager:
    """High-level AI manager with fallback support"""

    def __init__(self):
        self.settings = get_ai_settings()
        self.current_provider: AIProvider | None = None

    async def get_provider(self, provider_name: str | None = None) -> AIProvider:
        """Get or create a provider instance"""
        provider_name = provider_name or self.settings.ai_provider

        try:
            return create_ai_provider(provider_name)
        except (AIProviderError, ValueError) as e:
            logger.warning(f"Failed to create provider {provider_name}: {e}")

            if self.settings.enable_fallback:
                for fallback in self.settings.fallback_providers:
                    if fallback != provider_name:  # Don't retry the same provider
                        try:
                            logger.info(f"Trying fallback provider: {fallback}")
                            return create_ai_provider(fallback)
                        except Exception as fallback_error:
                            logger.warning(
                                f"Fallback provider {fallback} also failed: {fallback_error}"
                            )
                            continue

            raise AIProviderError(f"All AI providers failed. Last error: {e}", "all")

    async def generate_completion(
        self, messages: list[dict[str, str]], provider: str | None = None, **kwargs
    ) -> str:
        """Generate a completion with automatic fallback"""
        async with await self.get_provider(provider) as ai_provider:
            return await ai_provider.generate_completion(messages, **kwargs)

    async def stream_completion(
        self, messages: list[dict[str, str]], provider: str | None = None, **kwargs
    ) -> AsyncGenerator[str, None]:
        """Stream a completion with automatic fallback"""
        async with await self.get_provider(provider) as ai_provider:
            async for chunk in ai_provider.stream_completion(messages, **kwargs):
                yield chunk

    def get_available_providers(self) -> list[str]:
        """Get list of available providers"""
        return get_available_providers(self.settings)


# Global AI manager instance
ai_manager = AIManager()
