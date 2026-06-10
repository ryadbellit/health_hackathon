"""Minimal FastAPI app that sends an uploaded image to OpenAI and returns text."""

from __future__ import annotations

import base64
import os
from pathlib import Path

import json
import httpx
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv


load_dotenv(dotenv_path=Path(__file__).resolve().with_name(".env"))

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com")
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:4200").split(",")

app = FastAPI(title="server_2 openai image-to-text")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in CORS_ORIGINS if origin.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"status": "ok", "openai_configured": bool(OPENAI_API_KEY)}

@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    if not OPENAI_API_KEY:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY is not set")

    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Empty file")

    mime = file.content_type or "image/png"
    encoded = base64.b64encode(contents).decode("ascii")
    data_url = f"data:{mime};base64,{encoded}"

    payload = {
        "model": OPENAI_MODEL,
        "input": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": """
                        Extract and return the text content contained in this image. Return only the text. Output only english alphabet characters and numbers. 
                        Lean more towards medication names. Output strictly in the following JSON format:
                        ActiveIngredient: , 
                        Dosis: ,
                        Route: , 
                        Morning-Midday-Evening-Night: , 
                        AsNeeded: , 
                        Comment: ,

                        If information is missing, leave it empty and add a column after. Do not assume an information you are not certain of.
                        """,
                    },
                    {"type": "input_image", "image_url": data_url},
                ],
            }
        ],
    }

    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(base_url=OPENAI_BASE_URL, timeout=120.0) as client:
        resp = await client.post("/v1/responses", headers=headers, json=payload)

    if resp.status_code >= 400:
        raise HTTPException(status_code=502, detail=f"OpenAI error: {resp.status_code} {resp.text}")

    data = resp.json()
    raw_text = data.get("output_text", "")

    if not raw_text:
        output = data.get("output", [])
        for item in output:
            for content in item.get("content", []):
                if content.get("type") in {"output_text", "text"}:
                    raw_text = content.get("text", "")
                    if raw_text:
                        break
            if raw_text:
                break
    cleaned = raw_text.replace("```json", "").replace("```", "").strip()
    medication = json.loads(cleaned)
    return JSONResponse({"text": medication})
