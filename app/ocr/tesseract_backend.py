"""Tesseract OCR backend - uses local tessdata only.

pytesseract shells out to a local ``tesseract`` binary; ``TESSDATA_PREFIX``
must point at a local directory containing the language data files (no
network access is involved).
"""

from __future__ import annotations

import os

from PIL import Image

from app.config import Settings
from app.ocr.base import OCRResult


class TesseractBackend:
    def __init__(self, settings: Settings) -> None:
        try:
            import pytesseract
        except ImportError as exc:  # pragma: no cover - exercised only if missing
            raise RuntimeError(
                "OCR_ENGINE=tesseract but the 'pytesseract' package is not installed. "
                "See requirements-ocr.txt and docs/wiki/OCR-Setup.md."
            ) from exc

        if settings.TESSDATA_PREFIX:
            os.environ["TESSDATA_PREFIX"] = settings.TESSDATA_PREFIX

        self._pytesseract = pytesseract

    def run(self, image_path: str) -> OCRResult:
        with Image.open(image_path) as image:
            text = self._pytesseract.image_to_string(image)
        return OCRResult(text=text)
