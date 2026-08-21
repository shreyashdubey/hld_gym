"""The voice service. Holds the OpenAI key; the browser never sees it.

Dictation and Playground are the same pipeline with different stages, so they
are one service rather than two. See docs/superpowers/specs/2026-08-21-playground-design.md
"""

import os

from dotenv import load_dotenv
from fastapi import FastAPI

load_dotenv()

app = FastAPI(title="HLD Gym Playground")


@app.get("/health")
async def health() -> dict:
    """Reports whether a key is loaded. Never reports what the key is."""
    return {"ok": True, "key_loaded": bool(os.getenv("OPENAI_API_KEY"))}
