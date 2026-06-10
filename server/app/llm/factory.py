"""Factory for selecting an LLM client based on configuration."""

from __future__ import annotations

from server.app.config import Settings
from server.app.llm.base import LLMClient


def get_llm_client(settings: Settings) -> LLMClient:
    if settings.LLM_BACKEND == "ollama":
        from server.app.llm.ollama_client import OllamaVisionClient

        return OllamaVisionClient(settings)

    if settings.LLM_BACKEND == "gemini":
        from server.app.llm.gemini_client import GeminiVisionClient

        return GeminiVisionClient(settings)

    raise ValueError(f"Unsupported LLM_BACKEND: {settings.LLM_BACKEND!r}")
