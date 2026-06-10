import os

import pytest

from server.app.config import Settings
from server.app.pipeline import process_upload
from server.app.schema import MedicationEntry

SAMPLE_ENTRY = MedicationEntry(
    trade_name="Novalgin",
    active_ingredient="Metamizole",
    dosis="500 mg",
    route="oral",
    morning=1,
    midday=0,
    evening=1,
    night=0,
    as_needed="Yes",
    comment="Take as needed for pain; maximum 4 doses per day",
)


class StubLLMClient:
    def __init__(self, entries=None, error=None):
        self._entries = entries or []
        self._error = error

    def parse_image(self, image_bytes: bytes):
        if self._error:
            raise self._error
        return self._entries


@pytest.fixture
def settings(upload_tmp_dir):
    return Settings(UPLOAD_TMP_DIR=str(upload_tmp_dir))


def test_process_upload_returns_entries_and_cleans_up(settings, sample_png_bytes):
    client = StubLLMClient(entries=[SAMPLE_ENTRY])

    entries = process_upload(sample_png_bytes, settings, client)

    assert entries == [SAMPLE_ENTRY]
    assert os.listdir(settings.UPLOAD_TMP_DIR) == []


def test_process_upload_cleans_up_on_error(settings, sample_png_bytes):
    client = StubLLMClient(error=RuntimeError("boom"))

    with pytest.raises(RuntimeError, match="boom"):
        process_upload(sample_png_bytes, settings, client)

    assert os.listdir(settings.UPLOAD_TMP_DIR) == []


def test_process_upload_does_not_log_medication_content(settings, sample_png_bytes, caplog):
    client = StubLLMClient(entries=[SAMPLE_ENTRY])

    with caplog.at_level("DEBUG"):
        process_upload(sample_png_bytes, settings, client)

    log_text = "\n".join(record.getMessage() for record in caplog.records)
    assert "Novalgin" not in log_text
    assert "Metamizole" not in log_text
