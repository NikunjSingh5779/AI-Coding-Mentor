from __future__ import annotations

import json

import httpx

class MentorProviderError(RuntimeError):
    """LLM provider failed or returned invalid content."""

class MentorClient:
    def __init__(self, base_url: str, api_key: str, model: str, timeout: float = 30.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.timeout = timeout

    async def _resolve_model(self, client: httpx.AsyncClient, headers: dict[str, str]) -> str:
        if self.model and self.model != "auto":
            return self.model
        response = await client.get(f"{self.base_url}/models", headers=headers)
        response.raise_for_status()
        models = response.json().get("data", [])
        if not models:
            raise MentorProviderError("No model is available")
        return str(models[0].get("id", "auto"))

    async def generate(
        self,
        messages: list[dict[str, str]],
        *,
        max_tokens: int,
        temperature: float,
    ) -> str:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                model = await self._resolve_model(client, headers)
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json={
                        "model": model,
                        "messages": messages,
                        "max_tokens": max_tokens,
                        "temperature": temperature,
                        "stream": False,
                    },
                )
                response.raise_for_status()
                content = response.json()["choices"][0]["message"]["content"]
                if not isinstance(content, str) or not content.strip():
                    raise MentorProviderError("Empty LLM response")
                return content
        except (httpx.HTTPError, KeyError, TypeError, ValueError) as exc:
            raise MentorProviderError(str(exc)) from exc

def extract_json_object(text: str) -> dict:
    start = text.find("{")
    if start < 0:
        raise MentorProviderError("LLM did not return JSON")
    depth = 0
    for index in range(start, len(text)):
        if text[index] == "{":
            depth += 1
        elif text[index] == "}":
            depth -= 1
            if depth == 0:
                return json.loads(text[start:index + 1])
    raise MentorProviderError("Unbalanced JSON from LLM")
