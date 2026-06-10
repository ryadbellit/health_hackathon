# server_2 — minimal OpenAI image-to-text service

This is a tiny FastAPI service that accepts an image file and forwards it
to the OpenAI Responses API to extract text.

Requirements
- Python 3.11+ recommended
- See `requirements.txt` for packages

Setup
1. Create or edit `.env` and set `OPENAI_API_KEY`.
2. (Optional) Edit `CORS_ORIGINS` if your frontend runs on a different origin.

Run (PowerShell)
```powershell
cd server_2
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
# set env from .env or export OPENAI_API_KEY before starting
uvicorn main:app --reload --host 127.0.0.1 --port 8001
```

Endpoint
- `POST /upload` — form field `file` (image). Returns JSON: `{ "text": "extracted text", "raw": <openai response> }`.

Security
- Do not commit your `OPENAI_API_KEY`. Keep it in `server_2/.env`.
