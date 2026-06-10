# Architecture

```
client --PNG--> POST /upload --> app/main.py
                                    |
                                    v
                              app/pipeline.py
                                    |
                  +-----------------+------------------+
                  |                                     |
           write temp file                      app/llm/ollama_client.py
           (UPLOAD_TMP_DIR)                       --> http://127.0.0.1:11434
                  |                                (local Ollama, vision model)
           delete in `finally`
                  |
                  v
        list[MedicationEntry] (app/schema.py)
                  |
                  v
       JSON ({"medications": [...]}) or CSV
```

## Components

- **`app/config.py`** - `Settings` (pydantic-settings). Single source of truth
  for `OFFLINE_MODE`, allowed hosts, LLM/OCR configuration, and the upload
  temp directory. Validates at startup that the configured LLM URL is
  loopback-only when `OFFLINE_MODE=true`.
- **`app/network_guard.py`** - `install_network_guard()` patches
  `socket.socket.connect` so any non-loopback connection raises
  `OfflineModeBlockedError` while `OFFLINE_MODE=true`. Also sets
  `HF_HUB_OFFLINE`/`TRANSFORMERS_OFFLINE`/etc. defensively. See
  [Offline-Mode.md](Offline-Mode.md).
- **`app/schema.py`** - the fixed `MedicationEntry` model and
  `medications_to_csv()`, matching the required CSV header:
  `trade name,active ingredient,dosis,route,morning,midday,evening,night,as needed,Comment`.
- **`app/llm/ollama_client.py`** - `OllamaVisionClient` sends the uploaded
  image to a local Ollama vision model and validates the JSON response
  against `MedicationEntry`.
- **`app/ocr/`** - pluggable OCR backends (PaddleOCR, Tesseract), not used by
  the default pipeline yet. See [OCR-Setup.md](OCR-Setup.md) for how this
  would be wired in via `OCR_ENGINE`.
- **`app/pipeline.py`** - `process_upload()`: writes the upload to a temp
  file, runs the LLM client, and guarantees temp-file cleanup via `finally`.
  Logs only metadata (sizes, durations, row counts) - never raw content.
- **`app/main.py`** - FastAPI app. `GET /health`, `POST /upload`
  (`?format=json|csv`). Lifespan startup installs the network guard and
  builds the shared `Settings`/`OllamaVisionClient`.

## Future: switching to OCR-based parsing

The LLM-based path can be swapped for an OCR + rule-based extraction path by:

1. Adding a `PROCESSING_MODE` setting (`llm` | `ocr`) to `app/config.py`.
2. In `app/pipeline.py`, when `PROCESSING_MODE=ocr`, call
   `app.ocr.factory.get_ocr_backend(settings).run(tmp_path)` to get raw text,
   then parse that text into `list[MedicationEntry]`.

No changes to the API surface (`/upload`, response schema) would be required.
