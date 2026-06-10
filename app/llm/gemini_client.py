"""Cloud LLM client backed by the Google Gemini API.

DEMO ONLY. This client sends the uploaded image to a public Gemini endpoint
and is only constructible when ``OFFLINE_MODE=false`` (enforced by
``Settings._enforce_offline_mode``) - it must never be used with real patient
data on the intranet. For production, use ``app.llm.ollama_client`` instead.
"""

from __future__ import annotations

import base64

import httpx

from app.config import Settings
from app.llm.base import MEDICATION_EXTRACTION_PROMPT, parse_medication_entries
from app.schema import MedicationEntry


class GeminiVisionClient:
    def __init__(self, settings: Settings) -> None:
        if not settings.GEMINI_API_KEY:
            raise RuntimeError("LLM_BACKEND=gemini requires GEMINI_API_KEY to be set")

        self._api_key = settings.GEMINI_API_KEY
        self._model = settings.GEMINI_MODEL
        self._client = httpx.Client(base_url=settings.GEMINI_BASE_URL, timeout=120.0)

    def close(self) -> None:
        self._client.close()

    def parse_image(self, image_bytes: bytes) -> list[MedicationEntry]:
        encoded_image = base64.b64encode(image_bytes).decode("ascii")

        response = self._client.post(
            f"/v1beta/models/{self._model}:generateContent",
            params={"key": self._api_key},
            json={
                "contents": [
                    {
                        "parts": [
                            {"text": MEDICATION_EXTRACTION_PROMPT},
                            {
                                "inline_data": {
                                    "mime_type": "image/png",
                                    "data": encoded_image,
                                }
                            },
                        ]
                    }
                ],
                "generationConfig": {"response_mime_type": "application/json"},
            },
        )
        response.raise_for_status()

        candidates = response.json().get("candidates", [])
        raw_text = ""
        if candidates:
            parts = candidates[0].get("content", {}).get("parts", [])
            if parts:
                raw_text = parts[0].get("text", "")

        return parse_medication_entries(raw_text)
