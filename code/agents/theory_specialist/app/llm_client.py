"""
Unified LLM client for Ollama, OpenAI, and Gemini backends.
"""

from __future__ import annotations

import logging
from typing import Optional

import requests

from .config import Settings
from .ollama_client import OllamaClient


def _sanitize_api_key(api_key: Optional[str], show_last: int = 4) -> str:
    """Sanitize API key for logging by showing only last N characters."""
    if not api_key:
        return "(none)"
    if len(api_key) <= show_last:
        return "***"
    return f"***{api_key[-show_last:]}"


class OpenAIClient:
    def __init__(
        self,
        api_key: str,
        model: str,
        base_url: str = "https://api.openai.com",
        timeout: int = 60,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.logger = logging.getLogger(self.__class__.__name__)
        self.session = requests.Session()
        self.logger.info(
            "Initialized OpenAI client with model=%s, base_url=%s, api_key=%s",
            model,
            base_url,
            _sanitize_api_key(api_key),
        )

    def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        options: Optional[dict] = None,
    ) -> str:
        if not self.api_key:
            self.logger.error("OpenAI API key not configured")
            raise ValueError("OPENAI_API_KEY is required for OpenAI provider.")

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        payload: dict[str, object] = {
            "model": self.model,
            "messages": messages,
        }
        if options:
            if "temperature" in options:
                payload["temperature"] = options["temperature"]
            if "top_p" in options:
                payload["top_p"] = options["top_p"]
            if "max_tokens" in options:
                payload["max_tokens"] = options["max_tokens"]

        url = f"{self.base_url}/v1/chat/completions"
        try:
            response = self.session.post(
                url,
                headers={"Authorization": f"Bearer {self.api_key}"},
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()
        except requests.exceptions.RequestException as exc:
            self.logger.error(
                "OpenAI API request failed: %s (api_key=%s, model=%s)",
                str(exc),
                _sanitize_api_key(self.api_key),
                self.model,
            )
            raise
        data = response.json()
        try:
            return data["choices"][0]["message"]["content"].strip()
        except (KeyError, IndexError, TypeError) as exc:
            self.logger.error("Unexpected OpenAI response structure")
            raise ValueError("Invalid OpenAI response payload") from exc


class GeminiClient:
    def __init__(
        self,
        api_key: str,
        model: str,
        base_url: str = "https://generativelanguage.googleapis.com",
        timeout: int = 60,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.logger = logging.getLogger(self.__class__.__name__)
        self.session = requests.Session()
        self.logger.info(
            "Initialized Gemini client with model=%s, base_url=%s, api_key=%s",
            model,
            base_url,
            _sanitize_api_key(api_key),
        )

    def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        options: Optional[dict] = None,
    ) -> str:
        if not self.api_key:
            self.logger.error("Gemini API key not configured")
            raise ValueError("GEMINI_API_KEY is required for Gemini provider.")

        payload: dict[str, object] = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": prompt}],
                }
            ]
        }
        if system:
            payload["systemInstruction"] = {"parts": [{"text": system}]}
        if options:
            generation: dict[str, object] = {}
            if "temperature" in options:
                generation["temperature"] = options["temperature"]
            if "top_p" in options:
                generation["topP"] = options["top_p"]
            if "top_k" in options:
                generation["topK"] = options["top_k"]
            if "max_tokens" in options:
                generation["maxOutputTokens"] = options["max_tokens"]
            if generation:
                payload["generationConfig"] = generation

        url = f"{self.base_url}/v1beta/models/{self.model}:generateContent"
        try:
            response = self.session.post(
                url,
                params={"key": self.api_key},
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()
        except requests.exceptions.RequestException as exc:
            self.logger.error(
                "Gemini API request failed: %s (api_key=%s, model=%s)",
                str(exc),
                _sanitize_api_key(self.api_key),
                self.model,
            )
            raise
        data = response.json()
        try:
            return data["candidates"][0]["content"]["parts"][0]["text"].strip()
        except (KeyError, IndexError, TypeError) as exc:
            self.logger.error("Unexpected Gemini response structure")
            raise ValueError("Invalid Gemini response payload") from exc


def build_llm_client(settings: Settings):
    provider = (settings.llm_provider or "ollama").lower().strip()
    if provider == "openai":
        return OpenAIClient(
            api_key=settings.openai_api_key,
            model=settings.openai_model,
            base_url=settings.openai_base_url,
            timeout=settings.ollama_request_timeout,
        )
    if provider == "gemini":
        return GeminiClient(
            api_key=settings.gemini_api_key,
            model=settings.gemini_model,
            base_url=settings.gemini_base_url,
            timeout=settings.ollama_request_timeout,
        )
    if provider in ("ollama-cloud", "ollama_cloud"):
        base_url = settings.ollama_url
        if base_url.startswith(("http://127.0.0.1", "http://localhost")):
            base_url = "https://ollama.com"
    else:
        base_url = settings.ollama_url

    return OllamaClient(
        base_url=base_url,
        model=settings.ollama_model,
        timeout=settings.ollama_request_timeout,
        api_key=getattr(settings, "ollama_api_key", ""),
        use_chat=getattr(settings, "ollama_use_chat", True),
    )
