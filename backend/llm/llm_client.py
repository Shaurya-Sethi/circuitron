from __future__ import annotations

import os
from abc import ABC, abstractmethod
from typing import Iterable


class LLMClient(ABC):
    """Abstract base class for LLM clients."""

    @abstractmethod
    async def generate(self, prompt: str) -> str:
        """Generate completion from prompt."""

    @abstractmethod
    async def chat(self, messages: Iterable[dict[str, str]]) -> str:
        """Chat-style completion."""


class OpenRouterClient(LLMClient):
    """Stub client for OpenRouter API."""

    api_key_env = "OPENROUTER_API_KEY"

    def __init__(self) -> None:
        self.api_key = os.getenv(self.api_key_env)

    async def generate(self, prompt: str) -> str:
        # TODO(codex): integrate real API call
        return f"Generated response for: {prompt}" if self.api_key else ""

    async def chat(self, messages: Iterable[dict[str, str]]) -> str:
        # TODO(codex): integrate real API call
        joined = " ".join(m.get("content", "") for m in messages)
        return f"Chat response for: {joined}" if self.api_key else ""
