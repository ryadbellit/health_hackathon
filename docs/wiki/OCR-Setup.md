# OCR Setup (future use)

The default pipeline parses medication plans with a local vision LLM
(`app/llm/ollama_client.py`). The `app/ocr/` package provides pluggable OCR
backends for a future OCR-based extraction path - both load models **only**
from local paths and never download anything at runtime.

## Directory layout

```
/opt/health_hackathon/models/
  ocr/                  # OCR_MODEL_DIR - generic OCR model dir (engine-specific use)
  paddleocr/
    det/                # PADDLEOCR_DET_MODEL_DIR
    rec/                # PADDLEOCR_REC_MODEL_DIR
    cls/                # PADDLEOCR_CLS_MODEL_DIR
  tessdata/             # TESSDATA_PREFIX (only if OCR_ENGINE=tesseract)
```

The `models/` directory in this repo mirrors this layout with placeholder
`.gitkeep` files for local development; in deployment these paths point at
`/opt/health_hackathon/models/...` as set in `.env.example`.

## PaddleOCR

1. On a machine with internet access, download the PaddleOCR detection,
   recognition, and angle-classification model directories (det/rec/cls) for
   your target language.
2. Copy those three directories onto the intranet host at the paths
   configured by `PADDLEOCR_DET_MODEL_DIR`, `PADDLEOCR_REC_MODEL_DIR`,
   `PADDLEOCR_CLS_MODEL_DIR`.
3. `app/ocr/paddleocr_backend.py` constructs `PaddleOCR(det_model_dir=...,
   rec_model_dir=..., cls_model_dir=..., use_gpu=False, show_log=False)` -
   passing explicit local directories (instead of a model name) means
   PaddleOCR loads from disk only and does not attempt a download.
4. Install the optional dependencies: `pip install -r requirements-ocr.txt`.

## Tesseract

1. Install the `tesseract` binary and the language data files
   (`*.traineddata`) onto the intranet host, e.g. under
   `/opt/health_hackathon/models/tessdata/`.
2. Set `TESSDATA_PREFIX` to that directory and `OCR_ENGINE=tesseract`.
3. `app/ocr/tesseract_backend.py` sets `os.environ["TESSDATA_PREFIX"]` from
   config before calling `pytesseract.image_to_string()`.

## Wiring an OCR backend into the pipeline

`app/ocr/factory.get_ocr_backend(settings)` returns the configured backend.
To use it in the pipeline instead of (or alongside) the LLM client, see the
"Future: switching to OCR-based parsing" section in
[Architecture.md](Architecture.md).
