"""Local LLM client backed by Ollama (http://127.0.0.1:11434 by default).

Ollama itself runs models entirely on the local machine - this client never
talks to anything but the configured loopback address, and OFFLINE_MODE's
network guard (app/network_guard.py) enforces that at the socket level
regardless.
"""

from __future__ import annotations

import base64

import httpx

from app.config import Settings
from app.llm.base import MEDICATION_EXTRACTION_PROMPT, parse_medication_entries
from app.schema import MedicationEntry


class OllamaVisionClient:
    def __init__(self, settings: Settings) -> None:
        self._model = settings.OLLAMA_MODEL
        self._client = httpx.Client(base_url=settings.OLLAMA_BASE_URL, timeout=120.0)

    def close(self) -> None:
        self._client.close()

    def parse_image(self, image_bytes: bytes) -> list[MedicationEntry]:
        encoded_image = base64.b64encode(image_bytes).decode("ascii")

        response = self._client.post(
            "/api/generate",
            json={
                "model": self._model,
                "prompt": MEDICATION_EXTRACTION_PROMPT,
                "images": [encoded_image],
                "format": "json",
                "stream": False,
            },
        )
        response.raise_for_status()

        raw_text = response.json().get("response", "")
        return parse_medication_entries(raw_text)
