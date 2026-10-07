"""Inference host for photo checks (B47).

One scoring route and a health check. The only caller is the server's
HostedImageScorer (B53). Nothing about prompts or thresholds lives here: the
server decides what a score means.

Privacy rules this file keeps:
  - The photo is the raw request body, read straight into memory. FastAPI's
    UploadFile is not used: it spools bodies above about 1 MB to a temporary
    file on disk.
  - Nothing here logs the body, and the prompt travels as a query parameter so
    the body never has to be parsed or echoed into an error.
  - Nothing is written to disk.
"""

from __future__ import annotations

import secrets
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query, Request
from pydantic import BaseModel

from app.config import settings
from app.scorer import InvalidImageError, OpenClipScorer


class ScoreResponse(BaseModel):
    score: float


@asynccontextmanager
async def lifespan(app: FastAPI):
    scorer = OpenClipScorer(settings.clip_model_name, settings.clip_pretrained, settings.device)
    scorer.load()
    scorer.warm()
    app.state.scorer = scorer
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)


def _check_transport_and_token(request: Request) -> None:
    if settings.require_https:
        scheme = request.headers.get("x-forwarded-proto", request.url.scheme)
        if scheme != "https":
            raise HTTPException(status_code=403, detail="HTTPS required")

    if not settings.token:
        # No token configured: refuse rather than run an open scoring route.
        raise HTTPException(status_code=401, detail="Unauthorized")
    header = request.headers.get("authorization", "")
    expected = f"Bearer {settings.token}"
    if not secrets.compare_digest(header.encode(), expected.encode()):
        raise HTTPException(status_code=401, detail="Unauthorized")


async def _read_body_capped(request: Request, limit: int) -> bytes:
    declared = request.headers.get("content-length")
    if declared is not None and declared.isdigit() and int(declared) > limit:
        raise HTTPException(status_code=413, detail="Image too large")
    chunks: list[bytes] = []
    size = 0
    async for chunk in request.stream():
        size += len(chunk)
        if size > limit:
            raise HTTPException(status_code=413, detail="Image too large")
        chunks.append(chunk)
    return b"".join(chunks)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "app": settings.app_name,
        "environment": settings.environment,
    }


@app.post("/score", response_model=ScoreResponse)
async def score(request: Request, prompt: str = Query(..., min_length=1, max_length=200)) -> ScoreResponse:
    _check_transport_and_token(request)
    image_bytes = await _read_body_capped(request, settings.max_image_bytes)
    if not image_bytes:
        raise HTTPException(status_code=400, detail="Empty body")
    try:
        value = app.state.scorer.score(image_bytes, prompt)
    except InvalidImageError as exc:
        raise HTTPException(status_code=400, detail="Could not decode image") from exc
    finally:
        del image_bytes
    return ScoreResponse(score=value)
