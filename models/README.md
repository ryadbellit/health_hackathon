# Local model directory layout

This directory mirrors the local model paths referenced in `.env.example` and
`app/config.py`. In a real deployment these live under
`/opt/health_hackathon/models/` (or wherever `OCR_MODEL_DIR` /
`PADDLEOCR_*_MODEL_DIR` point), pre-populated with model files copied onto the
intranet host - nothing here is downloaded at runtime.

```
models/
  ocr/                # OCR_MODEL_DIR
  paddleocr/
    det/              # PADDLEOCR_DET_MODEL_DIR
    rec/              # PADDLEOCR_REC_MODEL_DIR
    cls/              # PADDLEOCR_CLS_MODEL_DIR
```

See [docs/wiki/OCR-Setup.md](../docs/wiki/OCR-Setup.md) for how to populate
these directories.
