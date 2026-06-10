"""Factory for selecting an OCR backend based on configuration."""

from __future__ import annotations

from app.config import Settings
from app.ocr.base import OCRBackend


def get_ocr_backend(settings: Settings) -> OCRBackend:
    if settings.OCR_ENGINE == "paddleocr":
        from app.ocr.paddleocr_backend import PaddleOCRBackend

        return PaddleOCRBackend(settings)

    if settings.OCR_ENGINE == "tesseract":
        from app.ocr.tesseract_backend import TesseractBackend

        return TesseractBackend(settings)

    raise ValueError(f"Unsupported OCR_ENGINE: {settings.OCR_ENGINE!r}")
