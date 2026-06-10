import pytest
from fastapi.testclient import TestClient

from app.llm.ollama_client import OllamaVisionClient
from app.main import app
from app.schema import MedicationEntry

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


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(
        OllamaVisionClient, "parse_image", lambda self, image_bytes: [SAMPLE_ENTRY]
    )
    with TestClient(app) as test_client:
        yield test_client


def test_health(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "offline_mode": True}


def test_upload_returns_medication_json(client, sample_png_bytes):
    response = client.post(
        "/upload", files={"file": ("plan.png", sample_png_bytes, "image/png")}
    )

    assert response.status_code == 200
    assert response.json() == {"medications": [SAMPLE_ENTRY.model_dump()]}


def test_upload_returns_medication_csv(client, sample_png_bytes):
    response = client.post(
        "/upload?format=csv",
        files={"file": ("plan.png", sample_png_bytes, "image/png")},
    )

    assert response.status_code == 200
    lines = response.text.splitlines()
    assert lines[0] == (
        "trade name,active ingredient,dosis,route,morning,midday,evening,night,as needed,Comment"
    )
    assert lines[1].startswith("Novalgin,Metamizole,500 mg,oral,")


def test_upload_rejects_non_png(client):
    response = client.post(
        "/upload", files={"file": ("plan.txt", b"not a png", "text/plain")}
    )

    assert response.status_code == 400
