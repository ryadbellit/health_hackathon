"""FastAPI application entrypoint."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query, UploadFile
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware

from server.app.config import Settings, get_settings
from server.app.llm.factory import get_llm_client
from server.app.logging_config import configure_logging, log_event
from server.app.network_guard import install_network_guard
from server.app.pipeline import process_upload
from server.app.schema import medications_to_csv

logger = logging.getLogger(__name__)

_PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


def _check_local_model_paths(settings: Settings) -> None:
    if settings.OCR_ENGINE == "paddleocr":
        for name, path in (
            ("PADDLEOCR_DET_MODEL_DIR", settings.PADDLEOCR_DET_MODEL_DIR),
            ("PADDLEOCR_REC_MODEL_DIR", settings.PADDLEOCR_REC_MODEL_DIR),
            ("PADDLEOCR_CLS_MODEL_DIR", settings.PADDLEOCR_CLS_MODEL_DIR),
        ):
            if not Path(path).is_dir():
                log_event(logger, "ocr_model_dir_missing", setting=name)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    configure_logging()
    install_network_guard(settings)
    _check_local_model_paths(settings)

    app.state.settings = settings
    # Enable CORS for local frontend dev origin(s)
    origins = [
        "http://localhost:4200",
        "http://127.0.0.1:4200",
    ]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.state.llm_client = get_llm_client(settings)
    log_event(
        logger, "app_startup", offline_mode=settings.OFFLINE_MODE, llm_backend=settings.LLM_BACKEND
    )
    try:
        yield
    finally:
        app.state.llm_client.close()


app = FastAPI(title="health_hackathon offline document parser", lifespan=lifespan)


@app.get("/health")
def health() -> dict:
    settings: Settings = app.state.settings
    return {"status": "ok", "offline_mode": settings.OFFLINE_MODE}


@app.post("/upload")
async def upload(
    file: UploadFile, format: str = Query("json", pattern="^(json|csv)$")
):
    if file.content_type != "image/png":
        raise HTTPException(status_code=400, detail="Only PNG images are supported")

    image_bytes = await file.read()
    if not image_bytes.startswith(_PNG_MAGIC):
        raise HTTPException(status_code=400, detail="File is not a valid PNG image")

    settings: Settings = app.state.settings
    llm_client = app.state.llm_client

    entries = process_upload(image_bytes, settings, llm_client)

    if format == "csv":
        return PlainTextResponse(medications_to_csv(entries), media_type="text/csv")

    return JSONResponse({"medications": [entry.model_dump() for entry in entries]})
