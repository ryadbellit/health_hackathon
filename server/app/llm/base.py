"""LLM client protocol and shared prompt/response-parsing helpers."""

from __future__ import annotations

import json
import logging
from typing import Protocol

from pydantic import ValidationError

from server.app.logging_config import log_event
from server.app.schema import MedicationEntry

logger = logging.getLogger(__name__)


class LLMClient(Protocol):
    def parse_image(self, image_bytes: bytes) -> list[MedicationEntry]:
        """Extract medication entries from an image of a medication plan."""
        ...

    def close(self) -> None:
        """Release any resources (HTTP clients, etc.)."""
        ...


MEDICATION_EXTRACTION_PROMPT = """\
You are reading a medication plan from a scanned image. Extract every \
medication row into a JSON array. Each element must be a JSON object with \
exactly these fields:

- trade_name: string, the brand/trade name of the medication
- active_ingredient: string, the active pharmaceutical ingredient
- dosis: string, the dose strength (e.g. "500 mg")
- route: string, the route of administration (e.g. "oral")
- morning: number, dose units taken in the morning (0 if none)
- midday: number, dose units taken at midday (0 if none)
- evening: number, dose units taken in the evening (0 if none)
- night: number, dose units taken at night (0 if none)
- as_needed: "Yes" or "No", whether this medication is taken as needed
- comment: string, any additional instructions (empty string if none)

Respond with ONLY the JSON array, no other text. Example of one element:
{"trade_name": "Novalgin", "active_ingredient": "Metamizole", "dosis": "500 mg", \
"route": "oral", "morning": 1, "midday": 0, "evening": 1, "night": 0, \
"as_needed": "Yes", "comment": "Take as needed for pain; maximum 4 doses per day"}
"""


def parse_medication_entries(raw_text: str) -> list[MedicationEntry]:
    """Parse a JSON array of medication rows from an LLM response.

    Tolerant of a top-level object wrapping the array (e.g.
    ``{"medications": [...]}``\\ ). Rows that fail validation are dropped.
    Only counts are logged - never the row content.
    """
    try:
        rows = json.loads(raw_text)
    except json.JSONDecodeError:
        log_event(logger, "llm_response_not_json")
        return []

    if isinstance(rows, dict):
        rows = next((v for v in rows.values() if isinstance(v, list)), [])

    if not isinstance(rows, list):
        log_event(logger, "llm_response_unexpected_shape")
        return []

    entries: list[MedicationEntry] = []
    skipped = 0
    for row in rows:
        try:
            entries.append(MedicationEntry.model_validate(row))
        except ValidationError:
            skipped += 1

    log_event(logger, "llm_parse_complete", rows=len(entries), skipped=skipped)
    return entries
