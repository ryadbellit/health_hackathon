"""Document processing pipeline: temp file -> LLM parse -> cleanup.

The uploaded image is written to a temporary file under UPLOAD_TMP_DIR and
removed again in a ``finally`` block, regardless of whether processing
succeeds. Only safe metadata (sizes, durations, row counts) is logged - never
the image bytes or the parsed medication content.
"""

from __future__ import annotations

import logging
import os
import time
from pathlib import Path
from tempfile import NamedTemporaryFile

from server.app.config import Settings
from server.app.llm.base import LLMClient
from server.app.logging_config import log_event
from server.app.schema import MedicationEntry

logger = logging.getLogger(__name__)


def process_upload(
    image_bytes: bytes, settings: Settings, llm_client: LLMClient
) -> list[MedicationEntry]:
    upload_dir = Path(settings.UPLOAD_TMP_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)

    tmp = NamedTemporaryFile(dir=upload_dir, suffix=".png", delete=False)
    tmp_path = Path(tmp.name)
    try:
        os.chmod(tmp_path, 0o600)
        tmp.write(image_bytes)
        tmp.close()

        start = time.monotonic()
        try:
            entries = llm_client.parse_image(image_bytes)
        except Exception:
            log_event(logger, "upload_processing_failed", size_bytes=len(image_bytes))
            raise

        duration = time.monotonic() - start
        log_event(
            logger,
            "upload_processed",
            size_bytes=len(image_bytes),
            duration_s=round(duration, 3),
            rows=len(entries),
        )
        return entries
    finally:
        tmp_path.unlink(missing_ok=True)
