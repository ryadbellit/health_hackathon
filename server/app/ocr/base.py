"""OCR backend protocol.

OCR is not used by the default pipeline yet (the pipeline currently relies on
a local vision LLM, see app/llm/). These backends are wired up for future use
- see docs/wiki/OCR-Setup.md - and must always load models from local paths
only.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass
class OCRResult:
    text: str


class OCRBackend(Protocol):
    def run(self, image_path: str) -> OCRResult:
        """Run OCR on the image at ``image_path`` and return the extracted text."""
        ...
