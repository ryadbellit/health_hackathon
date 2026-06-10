# Offline Mode

This service is designed to run on a clinic intranet host with **no internet
access**, and to fail loudly rather than silently leak data if something tries
to reach the internet.

## The `OFFLINE_MODE` flag

Set in `.env` (see `.env.example`):

```
OFFLINE_MODE=true
ALLOWED_HOSTS=127.0.0.1,localhost,::1
```

When `OFFLINE_MODE=true` (the default):

1. **Config validation** (`app/config.py`) - at startup, `Settings` checks
   that `LLM_BACKEND=ollama` and that `OLLAMA_BASE_URL` resolves to a host in
   `ALLOWED_HOSTS`. Selecting a cloud `LLM_BACKEND` (e.g. `gemini`) while
   `OFFLINE_MODE=true` raises a config error and the app refuses to start.
2. **Network guard** (`app/network_guard.py`) - `install_network_guard()` is
   called from the FastAPI lifespan and patches `socket.socket.connect`. Any
   attempt to connect to a host that is neither in `ALLOWED_HOSTS` nor a
   loopback address (`127.0.0.0/8`, `::1`) raises `OfflineModeBlockedError`
   immediately - before any data is sent.
3. **Library telemetry/offline env vars** - the guard also sets
   `HF_HUB_OFFLINE=1`, `TRANSFORMERS_OFFLINE=1`, `HF_HUB_DISABLE_TELEMETRY=1`,
   and `HF_HUB_DISABLE_IMPLICIT_TOKEN=1` (if not already set), so that if a
   `transformers`/`huggingface_hub`-based component is added later it won't
   attempt update checks or implicit downloads.

## What's explicitly disallowed

Per the project requirements, the following must never be reachable, and the
guard above blocks all of them at the socket level regardless of how they're
invoked:

- OpenAI / Azure OpenAI APIs
- Google Vision / Document AI
- AWS Textract
- Hugging Face Hub model downloads
- Any other cloud OCR/LLM API

Code must not call `from_pretrained("model-name")` without
`local_files_only=True` and a local path; `app/ocr/paddleocr_backend.py`
configures `det_model_dir` / `rec_model_dir` / `cls_model_dir` explicitly so
PaddleOCR never attempts a download.

## Data handling

- **Temp files**: `app/pipeline.py` writes the uploaded image to
  `UPLOAD_TMP_DIR` with mode `0600` and deletes it in a `finally` block, so it
  is removed even if processing fails.
- **Logging**: `app/logging_config.py`'s `log_event()` only accepts scalar
  metadata (sizes, durations, counts, booleans). Raw OCR/LLM text and
  medication content must never be passed to a logger - see
  `tests/test_pipeline.py::test_process_upload_does_not_log_medication_content`.

## Demo mode (cloud LLM)

For demos without a local Ollama install, `LLM_BACKEND=gemini` calls the
public Gemini API instead. This is **only** allowed when `OFFLINE_MODE=false`
(set explicitly in `.env`) and `GEMINI_API_KEY` is configured - the same
config validator that pins `ollama` to loopback raises an error if `gemini`
is selected while `OFFLINE_MODE=true`.

**Do not use `LLM_BACKEND=gemini` with real patient data or on the intranet
deployment.** It exists purely so the demo works on a machine without Ollama.
For production, set `OFFLINE_MODE=true` and `LLM_BACKEND=ollama` (the
defaults) and run a local Ollama instance per
[Development.md](Development.md).

## Acceptance criteria checklist

- [x] App works with no internet connection (LLM runs locally via Ollama).
- [x] Starting the app does not trigger network requests (guard installed at
      startup; `OllamaVisionClient.__init__` only constructs an `httpx.Client`,
      it does not connect).
- [x] Uploading a PNG only talks to `OLLAMA_BASE_URL` (loopback).
- [x] `pytest.ini` runs the suite with
      `--disable-socket --allow-hosts=127.0.0.1,::1` - any external HTTP call
      in a test fails the suite.
