"""Logging setup.

Convention enforced by code review, not by a magic filter: callers must only
pass pre-approved scalar metadata to ``log_event`` (file sizes, durations,
counts, booleans, engine names, etc.). Raw OCR/LLM text, image bytes, and any
patient-identifying data must never be passed to a logger.
"""

from __future__ import annotations

import logging
import sys

_LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s %(message)s"


def configure_logging(level: int = logging.INFO) -> None:
    logging.basicConfig(
        level=level,
        format=_LOG_FORMAT,
        stream=sys.stdout,
        force=True,
    )


def log_event(logger: logging.Logger, event: str, **safe_fields: object) -> None:
    """Log a structured event using only safe (non-PHI) metadata fields."""
    fields = " ".join(f"{key}={value!r}" for key, value in safe_fields.items())
    logger.info("%s %s", event, fields)
