import pytest

from server.app.config import Settings


def test_offline_mode_defaults_true():
    settings = Settings()
    assert settings.OFFLINE_MODE is True
    assert "127.0.0.1" in settings.ALLOWED_HOSTS


def test_offline_mode_rejects_non_loopback_llm_url():
    with pytest.raises(ValueError, match="ALLOWED_HOSTS"):
        Settings(OFFLINE_MODE=True, OLLAMA_BASE_URL="http://api.openai.com")


def test_offline_mode_allows_loopback_llm_url():
    settings = Settings(OFFLINE_MODE=True, OLLAMA_BASE_URL="http://127.0.0.1:11434")
    assert settings.OLLAMA_BASE_URL == "http://127.0.0.1:11434"


def test_allowed_hosts_can_be_set_via_csv_string():
    settings = Settings(ALLOWED_HOSTS="127.0.0.1, localhost")
    assert settings.ALLOWED_HOSTS == ["127.0.0.1", "localhost"]


def test_offline_mode_rejects_cloud_llm_backend():
    with pytest.raises(ValueError, match="LLM_BACKEND"):
        Settings(OFFLINE_MODE=True, LLM_BACKEND="gemini", GEMINI_API_KEY="test-key")


def test_gemini_backend_requires_offline_mode_false_and_api_key():
    with pytest.raises(ValueError, match="GEMINI_API_KEY"):
        Settings(OFFLINE_MODE=False, LLM_BACKEND="gemini")


def test_gemini_backend_allowed_when_offline_mode_false_with_api_key():
    settings = Settings(OFFLINE_MODE=False, LLM_BACKEND="gemini", GEMINI_API_KEY="test-key")
    assert settings.LLM_BACKEND == "gemini"
    assert settings.GEMINI_API_KEY == "test-key"
