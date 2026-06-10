# Development

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

## Running the app

A local Ollama instance with a vision model (e.g. `llava`) is needed for
`/upload` to return real results:

```bash
ollama pull llava
ollama serve
uvicorn app.main:app --reload
```

`GET /health` works without Ollama running.

## Running the tests

```bash
pytest
```

`pytest.ini` adds `--disable-socket --allow-hosts=127.0.0.1,::1`: any test
that tries to open a socket to a host other than loopback fails with
`SocketBlockedError`. Tests that exercise `/upload` monkeypatch
`OllamaVisionClient.parse_image` so they don't depend on a running Ollama
instance.

## Project layout

See [Architecture.md](Architecture.md).

## Adding a new config value

Add it to `app/config.py`'s `Settings`, document the default in
`.env.example`, and if it's a value that could point off-host (a URL),
consider adding it to the `_enforce_offline_mode` validator.
