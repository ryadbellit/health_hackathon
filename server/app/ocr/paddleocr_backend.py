"""PaddleOCR backend - loads models only from local directories.

PaddleOCR is an optional dependency (see requirements-ocr.txt). The det/rec/cls
model directories must be pre-downloaded onto the local filesystem; passing
explicit local directories (rather than model names) prevents PaddleOCR from
attempting to download anything at runtime.
"""

from __future__ import annotations

from server.app.config import Settings
from server.app.ocr.base import OCRResult


class PaddleOCRBackend:
    def __init__(self, settings: Settings) -> None:
        try:
            from paddleocr import PaddleOCR
        except ImportError as exc:  # pragma: no cover - exercised only if missing
            raise RuntimeError(
                "OCR_ENGINE=paddleocr but the 'paddleocr' package is not installed. "
                "See requirements-ocr.txt and docs/wiki/OCR-Setup.md."
            ) from exc

        self._ocr = PaddleOCR(
            det_model_dir=settings.PADDLEOCR_DET_MODEL_DIR,
            rec_model_dir=settings.PADDLEOCR_REC_MODEL_DIR,
            cls_model_dir=settings.PADDLEOCR_CLS_MODEL_DIR,
            use_angle_cls=True,
            use_gpu=False,
            show_log=False,
        )

    def run(self, image_path: str) -> OCRResult:
        result = self._ocr.ocr(image_path, cls=True)
        lines = [
            line[1][0]
            for page in result
            for line in page
        ]
        return OCRResult(text="\n".join(lines))
