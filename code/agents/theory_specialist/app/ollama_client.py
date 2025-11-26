"""
Thin wrapper around the Ollama HTTP API.
"""

from __future__ import annotations

import logging
from typing import Optional

import requests


class OllamaClient:
    """Simple HTTP client for interacting with a local Ollama server."""

    def __init__(self, base_url: str, model: str, timeout: int = 60) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout
        self.logger = logging.getLogger(self.__class__.__name__)

    def generate(self, prompt: str, system: Optional[str] = None) -> str:
        """
        Generate a completion from the configured Ollama model.
        """
        payload: dict[str, object] = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
        }
        if system:
            payload["system"] = system

        url = f"{self.base_url}/api/generate"
        response = requests.post(url, json=payload, timeout=self.timeout)
        response.raise_for_status()
        data = response.json()
        output = data.get("response")
        if not isinstance(output, str):
            self.logger.error("Unexpected Ollama response: %s", data)
            raise ValueError("Invalid Ollama response payload")
        return output.strip()

