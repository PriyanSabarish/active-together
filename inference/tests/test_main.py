"""Route-contract tests for the inference host.

These never load a real model: app.state.scorer is replaced with a fake before
any request, and the client is never used as a context manager, so the
lifespan (which loads open_clip for real) never runs. The real OpenClipScorer
needs a manual check once the weights can be downloaded (see README).
"""

from __future__ import annotations

import io
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.config import settings
from app.main import app
from app.scorer import InvalidImageError

TOKEN = "test-token"
AUTH = {"Authorization": f"Bearer {TOKEN}"}


class FakeScorer:
    def __init__(self, value: float = 0.31, raise_invalid: bool = False):
        self._value = value
        self._raise_invalid = raise_invalid
        self.seen: list[tuple[int, str]] = []

    def score(self, image_bytes: bytes, prompt: str) -> float:
        self.seen.append((len(image_bytes), prompt))
        if self._raise_invalid:
            raise InvalidImageError("bad image")
        return self._value


def png_bytes() -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (8, 8), color=(1, 2, 3)).save(buffer, format="PNG")
    return buffer.getvalue()


@pytest.fixture(autouse=True)
def configured(monkeypatch):
    monkeypatch.setattr(settings, "token", TOKEN)
    monkeypatch.setattr(settings, "require_https", False)
    monkeypatch.setattr(settings, "max_image_bytes", 5 * 1024 * 1024)
    app.state.scorer = FakeScorer()


def client() -> TestClient:
    return TestClient(app)


def post(body: bytes | None = None, headers=AUTH, prompt="something red"):
    return client().post("/score", params={"prompt": prompt}, content=png_bytes() if body is None else body, headers=headers)


def test_health_needs_no_token():
    response = client().get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_score_returns_the_similarity_and_passes_the_prompt():
    app.state.scorer = FakeScorer(0.42)
    response = post()
    assert response.status_code == 200
    assert response.json() == {"score": 0.42}
    assert app.state.scorer.seen[0][1] == "something red"


def test_missing_wrong_or_malformed_token_is_rejected():
    assert post(headers={}).status_code == 401
    assert post(headers={"Authorization": "Bearer nope"}).status_code == 401
    assert post(headers={"Authorization": TOKEN}).status_code == 401
    assert app.state.scorer.seen == []


def test_no_token_configured_refuses_everything(monkeypatch):
    monkeypatch.setattr(settings, "token", None)
    assert post().status_code == 401
    assert post(headers={"Authorization": "Bearer "}).status_code == 401


def test_https_required_when_deployed(monkeypatch):
    monkeypatch.setattr(settings, "require_https", True)
    assert post().status_code == 403  # TestClient is plain http
    assert post(headers={**AUTH, "X-Forwarded-Proto": "https"}).status_code == 200
    assert post(headers={**AUTH, "X-Forwarded-Proto": "http"}).status_code == 403
    assert client().get("/health").status_code == 200


def test_oversized_body_is_rejected_before_scoring(monkeypatch):
    monkeypatch.setattr(settings, "max_image_bytes", 100)
    assert post(body=b"x" * 101).status_code == 413
    assert app.state.scorer.seen == []


def test_empty_body_is_a_bad_request():
    assert post(body=b"").status_code == 400


def test_undecodable_image_is_a_bad_request_without_echoing_it():
    app.state.scorer = FakeScorer(raise_invalid=True)
    response = post(body=b"not-an-image-SECRET")
    assert response.status_code == 400
    assert "SECRET" not in response.text


def test_missing_prompt_is_rejected():
    response = client().post("/score", content=png_bytes(), headers=AUTH)
    assert response.status_code == 422
    assert "SECRET" not in response.text


def test_large_photo_leaves_nothing_in_temp_directories():
    """A body well over the 1 MB spool limit still never touches disk."""
    tmp = Path(tempfile.gettempdir())
    before = {p.name for p in tmp.iterdir()}
    big = png_bytes() + b"\0" * (3 * 1024 * 1024)
    for _ in range(3):
        assert post(body=big).status_code == 200
    after = {p.name for p in tmp.iterdir()}
    assert after - before == set()
