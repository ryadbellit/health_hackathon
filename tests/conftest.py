import io

import pytest
from PIL import Image

from app.config import Settings


@pytest.fixture
def sample_png_bytes() -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (4, 4), color="white").save(buffer, format="PNG")
    return buffer.getvalue()


@pytest.fixture(autouse=True)
def _isolated_settings(monkeypatch, tmp_path):
    # The repo's real .env (demo Gemini config, OFFLINE_MODE=false) must never
    # leak into the test suite - tests rely on Settings() defaulting to
    # OFFLINE_MODE=true / LLM_BACKEND=ollama. Run from a directory with no
    # .env and clear any matching env vars from the shell.
    for name in Settings.model_fields:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.chdir(tmp_path)


@pytest.fixture(autouse=True)
def upload_tmp_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("UPLOAD_TMP_DIR", str(tmp_path / "uploads"))
    return tmp_path / "uploads"
