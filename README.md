# health_hackathon - Offline Medication Plan Parser

A FastAPI service that runs entirely inside the hospital/clinic intranet: it
accepts a photo/scan of a medication plan (PNG) and returns the medications as
structured JSON or CSV, using a **local** vision LLM (via [Ollama](https://ollama.com))
to do the parsing. No step in this pipeline calls out to the public internet.

See [docs/wiki/Home.md](docs/wiki/Home.md) for the full wiki.

## Quickstart

1. **Install dependencies**

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Configure**

   ```bash
   cp .env.example .env
   ```

   The defaults already enable `OFFLINE_MODE=true` and point the LLM client at
   `http://127.0.0.1:11434` (a local Ollama instance). Adjust `OLLAMA_MODEL`
   to whatever local vision model you have pulled, e.g. `ollama pull llava`.

3. **Run a local LLM server** (Ollama, on this machine, no internet required
   once the model is pulled):

   ```bash
   ollama serve
   ```

4. **Start the API**

   ```bash
   uvicorn app.main:app --reload
   ```

5. **Upload a medication plan**

   ```bash
   curl -F "file=@plan.png" "http://127.0.0.1:8000/upload"
   curl -F "file=@plan.png" "http://127.0.0.1:8000/upload?format=csv"
   ```

### Demo mode without Ollama (cloud LLM)

If you don't have Ollama installed, you can run the demo against the
free-tier [Google Gemini API](https://ai.google.dev/) instead. **This is for
demos with non-patient data only** - it sends the image to a public API and
is rejected by config validation unless you explicitly disable offline mode:

```bash
# .env
OFFLINE_MODE=false
LLM_BACKEND=gemini
GEMINI_API_KEY=your-free-api-key
```

Everything else (`/upload`, output format) is unchanged. For the real
intranet deployment, leave `OFFLINE_MODE=true` and `LLM_BACKEND=ollama` (the
defaults) - see [docs/wiki/Offline-Mode.md](docs/wiki/Offline-Mode.md).

## Output format

Each medication is returned as a row with these fields:

```
trade name,active ingredient,dosis,route,morning,midday,evening,night,as needed,Comment
Novalgin,Metamizole,500 mg,oral,1,0,1,0,Yes,Take as needed for pain; maximum 4 doses per day
```

`/upload` returns this as `{"medications": [...]}` JSON; `/upload?format=csv`
returns it as `text/csv`.

## Offline guarantees

- `OFFLINE_MODE=true` (default) actively blocks any outbound connection to a
  host outside `ALLOWED_HOSTS` (loopback only) - see
  [docs/wiki/Offline-Mode.md](docs/wiki/Offline-Mode.md).
- Uploaded images are written to a temp file and deleted immediately after
  processing.
- Logs never contain raw OCR/LLM text, image bytes, or medication content -
  only metadata (sizes, durations, row counts).
- OCR backends (PaddleOCR/Tesseract, for future use) load models only from
  local directories - see [docs/wiki/OCR-Setup.md](docs/wiki/OCR-Setup.md).

## Tests

```bash
pytest
```

`pytest.ini` runs the suite with `--disable-socket --allow-hosts=127.0.0.1,::1`,
so any test that attempts an external network call fails immediately. See
[docs/wiki/Development.md](docs/wiki/Development.md).
