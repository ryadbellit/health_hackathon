"""Fixed output schema for parsed medication plans."""

from __future__ import annotations

import csv
import io
from typing import Literal

from pydantic import BaseModel


class MedicationEntry(BaseModel):
    trade_name: str
    active_ingredient: str
    dosis: str
    route: str
    morning: float
    midday: float
    evening: float
    night: float
    as_needed: Literal["Yes", "No"]
    comment: str = ""


# Maps MedicationEntry fields (in order) to the fixed CSV header required by the
# downstream tooling. Order and header text must not change.
CSV_HEADER = [
    "trade name",
    "active ingredient",
    "dosis",
    "route",
    "morning",
    "midday",
    "evening",
    "night",
    "as needed",
    "Comment",
]

_FIELD_ORDER = [
    "trade_name",
    "active_ingredient",
    "dosis",
    "route",
    "morning",
    "midday",
    "evening",
    "night",
    "as_needed",
    "comment",
]


def medications_to_csv(entries: list[MedicationEntry]) -> str:
    """Serialize medication entries to CSV using the fixed header/column order."""
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(CSV_HEADER)
    for entry in entries:
        data = entry.model_dump()
        writer.writerow([data[field] for field in _FIELD_ORDER])
    return buffer.getvalue()
