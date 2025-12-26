"""
Thin wrapper around the Ollama HTTP API.
"""

from __future__ import annotations

import logging
from typing import Optional

import requests


class OllamaClient:
    """Simple HTTP client for interacting with a local Ollama server."""

    def __init__(
        self,
        base_url: str,
        model: str,
        timeout: int = 60,
        api_key: str | None = None,
        use_chat: bool = True,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout
        self.api_key = api_key or ""
        self.use_chat = use_chat
        self.logger = logging.getLogger(self.__class__.__name__)
        self.session = requests.Session()

    def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        options: Optional[dict] = None,
    ) -> str:
        """
        Generate a completion from the configured Ollama model.
        """
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        if self.use_chat:
            messages = []
            if system:
                messages.append({"role": "system", "content": system})
            messages.append({"role": "user", "content": prompt})
            payload: dict[str, object] = {
                "model": self.model,
                "messages": messages,
                "stream": False,
            }
            if options:
                ollama_options = dict(options)
                if "max_tokens" in ollama_options and "num_predict" not in ollama_options:
                    ollama_options["num_predict"] = ollama_options.pop("max_tokens")
                payload["options"] = ollama_options
            url = f"{self.base_url}/api/chat"
            response = self.session.post(
                url, json=payload, timeout=self.timeout, headers=headers
            )
            response.raise_for_status()
            data = response.json()
            try:
                return data["message"]["content"].strip()
            except (KeyError, TypeError) as exc:
                self.logger.error("Unexpected Ollama chat response: %s", data)
                raise ValueError("Invalid Ollama chat response payload") from exc

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
        }
        if system:
            payload["system"] = system
        if options:
            ollama_options = dict(options)
            if "max_tokens" in ollama_options and "num_predict" not in ollama_options:
                ollama_options["num_predict"] = ollama_options.pop("max_tokens")
            payload["options"] = ollama_options

        url = f"{self.base_url}/api/generate"
        response = self.session.post(url, json=payload, timeout=self.timeout, headers=headers)
        response.raise_for_status()
        data = response.json()
        output = data.get("response")
        if not isinstance(output, str):
            self.logger.error("Unexpected Ollama response: %s", data)
            raise ValueError("Invalid Ollama response payload")
        return output.strip()
