from __future__ import annotations

import json
import os
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

import httpx
from openai import OpenAI


class BaseProvider(ABC):
    def __init__(
        self,
        model: str,
        temperature: float = 0.6,
        top_p: float = 0.9,
        max_retries: int = 5,
    ) -> None:
        self.model = model
        self.temperature = temperature
        self.top_p = top_p
        self.max_retries = max_retries

    @abstractmethod
    def generate(self, system: str, user: str) -> str:
        """Return the raw LLM response text."""


class OpenAIProvider(BaseProvider):
    def __init__(self, model: str, **kwargs: Any) -> None:
        super().__init__(model, **kwargs)
        base_url = os.getenv("OPENAI_BASE_URL")
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY not set")
        self.client = OpenAI(api_key=api_key, base_url=base_url)

    def generate(self, system: str, user: str) -> str:
        last_error: Optional[Exception] = None
        for attempt in range(1, self.max_retries + 1):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    temperature=self.temperature,
                    top_p=self.top_p,
                    messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
                    response_format={"type": "json_object"} if user.strip().lower().startswith("return json") else None,
                )
                return response.choices[0].message.content or ""
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                time.sleep(1.5 * attempt)
        raise RuntimeError(f"OpenAI provider failed after {self.max_retries} attempts: {last_error}")


class OllamaProvider(BaseProvider):
    def __init__(self, model: str, **kwargs: Any) -> None:
        super().__init__(model, **kwargs)
        # Use hosted Ollama API instead of localhost
        self.base_url = os.getenv("OLLAMA_HOST", "https://ollama.com")
        self.headers: Dict[str, str] = {}
        api_key = os.getenv("OLLAMA_API_KEY")
        if api_key:
            self.headers["Authorization"] = f"Bearer {api_key}"
        # Increase timeout for hosted API
        self.client = httpx.Client(timeout=120.0)

    def generate(self, system: str, user: str) -> str:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "options": {
                "temperature": self.temperature,
                "top_p": self.top_p,
            },
            "stream": False,
        }
        last_error: Optional[Exception] = None
        for attempt in range(1, self.max_retries + 1):
            try:
                response = self.client.post(
                    f"{self.base_url}/api/chat",
                    json=payload,
                    headers=self.headers or None,
                )
                response.raise_for_status()
                data = response.json()
                return data.get("message", {}).get("content", "")
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                # Longer backoff for hosted API
                time.sleep(2.0 * attempt)
        raise RuntimeError(f"Ollama provider failed after {self.max_retries} attempts: {last_error}")


def build_provider(name: str, model: str, **kwargs: Any) -> BaseProvider:
    name = name.lower()
    if name == "openai":
        return OpenAIProvider(model=model, **kwargs)
    if name == "ollama":
        return OllamaProvider(model=model, **kwargs)
    raise ValueError(f"Unsupported provider '{name}'")
