"""Inference service scaffold (B37) — loads both models at startup, warms
them, and exposes one scoring route and one generation route.

This is the only thing HostedModelClient (B38) talks to. Nothing about model
choice, prompts, or thresholds belongs on the Backend A side of the wire.
"""

from __future__ import annotations

import json
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from app.config import settings
from app.generator import TextGenerator
from app.scorer import ClipScorer, InvalidImageError


class GenerateRequest(BaseModel):
    prompt: str
    max_tokens: int = 64
    timeout_s: int = 10


class GenerateResponse(BaseModel):
    text: str | None


class ScoreResponse(BaseModel):
    scores: list[float] | None


@asynccontextmanager
async def lifespan(app: FastAPI):
    scorer = ClipScorer(settings.clip_model_name, settings.device)
    generator = TextGenerator(settings.text_model_name, settings.device)

    scorer.load()
    scorer.warm()
    generator.load()
    generator.warm()

    app.state.scorer = scorer
    app.state.generator = generator
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "app": settings.app_name,
        "environment": settings.environment,
    }


@app.post("/generate", response_model=GenerateResponse)
def generate(req: GenerateRequest) -> GenerateResponse:
    text = app.state.generator.generate(req.prompt, req.max_tokens, req.timeout_s)
    return GenerateResponse(text=text)


@app.post("/score", response_model=ScoreResponse)
async def score(image: UploadFile = File(...), prompts: str = Form(...)) -> ScoreResponse:
    try:
        prompt_list = json.loads(prompts)
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=400, detail="prompts must be a JSON-encoded list of strings"
        ) from exc

    if not isinstance(prompt_list, list) or not all(isinstance(p, str) for p in prompt_list):
        raise HTTPException(status_code=400, detail="prompts must be a JSON list of strings")

    image_bytes = await image.read()
    try:
        scores = app.state.scorer.score(image_bytes, prompt_list)
    except InvalidImageError as exc:
        raise HTTPException(status_code=400, detail="Could not decode image") from exc

    return ScoreResponse(scores=scores)
