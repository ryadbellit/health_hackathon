import json

import httpx
import pytest

from app.config import Settings
from app.llm.gemini_client import GeminiVisionClient


@pytest.fixture
def settings():
    return Settings(OFFLINE_MODE=False, LLM_BACKEND="gemini", GEMINI_API_KEY="test-key")


def test_parse_image_returns_validated_entries(settings, sample_png_bytes, monkeypatch):
    medication_row = {
        "trade_name": "Novalgin",
        "active_ingredient": "Metamizole",
        "dosis": "500 mg",
        "route": "oral",
        "morning": 1,
        "midday": 0,
        "evening": 1,
        "night": 0,
        "as_needed": "Yes",
        "comment": "Take as needed for pain; maximum 4 doses per day",
    }

    def fake_post(self, url, **kwargs):
        body = {
            "candidates": [
                {"content": {"parts": [{"text": json.dumps([medication_row])}]}}
            ]
        }
        return httpx.Response(200, json=body, request=httpx.Request("POST", "https://example.test" + url))

    monkeypatch.setattr(httpx.Client, "post", fake_post)

    client = GeminiVisionClient(settings)
    try:
        entries = client.parse_image(sample_png_bytes)
    finally:
        client.close()

    assert len(entries) == 1
    assert entries[0].trade_name == "Novalgin"


def test_parse_image_handles_non_json_response(settings, sample_png_bytes, monkeypatch):
    def fake_post(self, url, **kwargs):
        body = {"candidates": [{"content": {"parts": [{"text": "not json"}]}}]}
        return httpx.Response(200, json=body, request=httpx.Request("POST", "https://example.test" + url))

    monkeypatch.setattr(httpx.Client, "post", fake_post)

    client = GeminiVisionClient(settings)
    try:
        entries = client.parse_image(sample_png_bytes)
    finally:
        client.close()

    assert entries == []


def test_constructor_requires_api_key():
    settings = Settings(OFFLINE_MODE=False, LLM_BACKEND="gemini", GEMINI_API_KEY="placeholder")
    settings.GEMINI_API_KEY = None  # bypass the Settings validator for this unit check

    with pytest.raises(RuntimeError, match="GEMINI_API_KEY"):
        GeminiVisionClient(settings)
