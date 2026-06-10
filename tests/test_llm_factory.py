from app.config import Settings
from app.llm.factory import get_llm_client
from app.llm.gemini_client import GeminiVisionClient
from app.llm.ollama_client import OllamaVisionClient


def test_factory_returns_ollama_client_by_default():
    settings = Settings()
    client = get_llm_client(settings)
    try:
        assert isinstance(client, OllamaVisionClient)
    finally:
        client.close()


def test_factory_returns_gemini_client_when_configured():
    settings = Settings(OFFLINE_MODE=False, LLM_BACKEND="gemini", GEMINI_API_KEY="test-key")
    client = get_llm_client(settings)
    try:
        assert isinstance(client, GeminiVisionClient)
    finally:
        client.close()
