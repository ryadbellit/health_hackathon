"""Application configuration.

All settings are loaded from environment variables / a local .env file. Nothing
here ever points at a remote/cloud service by default - see docs/wiki/Offline-Mode.md.
"""

from __future__ import annotations

from typing import Annotated, Literal
from urllib.parse import urlparse

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # --- Offline / network ---
    # Default to allowing network access so the Gemini backend can be used
    # (set OFFLINE_MODE=true in your .env to force local-only mode).
    OFFLINE_MODE: bool = False
    # NoDecode: take the raw env string as-is (e.g. "127.0.0.1,localhost") instead
    # of pydantic-settings' default JSON decoding for list fields, so the
    # comma-separated form in .env.example works.
    ALLOWED_HOSTS: Annotated[list[str], NoDecode] = ["127.0.0.1", "localhost", "::1"]

    # --- LLM ---
    # "ollama" runs fully locally and is the only backend allowed when
    # OFFLINE_MODE=true. "gemini" calls the Google Gemini API and requires
    # OFFLINE_MODE=false - intended for demos only, not for real patient data
    # on the intranet. See docs/wiki/Offline-Mode.md.
    # Default to Gemini for demo purposes. Ensure GEMINI_API_KEY is set.
    LLM_BACKEND: Literal["ollama", "gemini"] = "gemini"
    OLLAMA_BASE_URL: str = "http://127.0.0.1:11434"
    OLLAMA_MODEL: str = "llava"

    GEMINI_API_KEY: str | None = None
    GEMINI_MODEL: str = "gemini-2.0-flash"
    GEMINI_BASE_URL: str = "https://generativelanguage.googleapis.com"

    # --- OCR (future use, pluggable) ---
    OCR_ENGINE: Literal["paddleocr", "tesseract"] = "paddleocr"
    OCR_MODEL_DIR: str = "/opt/health_hackathon/models/ocr"
    PADDLEOCR_DET_MODEL_DIR: str = "/opt/health_hackathon/models/paddleocr/det"
    PADDLEOCR_REC_MODEL_DIR: str = "/opt/health_hackathon/models/paddleocr/rec"
    PADDLEOCR_CLS_MODEL_DIR: str = "/opt/health_hackathon/models/paddleocr/cls"
    TESSDATA_PREFIX: str | None = None

    # --- Uploads ---
    UPLOAD_TMP_DIR: str = "/tmp/health_hackathon_uploads"

    @field_validator("ALLOWED_HOSTS", mode="before")
    @classmethod
    def _split_allowed_hosts(cls, value: object) -> object:
        if isinstance(value, str):
            return [host.strip() for host in value.split(",") if host.strip()]
        return value

    @model_validator(mode="after")
    def _enforce_offline_mode(self) -> "Settings":
        if self.OFFLINE_MODE:
            if self.LLM_BACKEND != "ollama":
                raise ValueError(
                    f"OFFLINE_MODE is enabled but LLM_BACKEND={self.LLM_BACKEND!r} "
                    "calls an external API. Use LLM_BACKEND=ollama (local-only), "
                    "or set OFFLINE_MODE=false to allow a cloud LLM backend."
                )

            for url in (self.OLLAMA_BASE_URL,):
                host = urlparse(url).hostname
                if host not in self.ALLOWED_HOSTS:
                    raise ValueError(
                        f"OFFLINE_MODE is enabled but {url!r} points at host "
                        f"{host!r}, which is not in ALLOWED_HOSTS={self.ALLOWED_HOSTS}. "
                        "Local services must be reachable on a loopback address."
                    )
        else:
            if self.LLM_BACKEND == "gemini" and not self.GEMINI_API_KEY:
                raise ValueError("LLM_BACKEND=gemini requires GEMINI_API_KEY to be set")

        return self


def get_settings() -> Settings:
    return Settings()
