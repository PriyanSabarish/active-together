"""Route-contract tests for the inference service.

These never load a real model: app.state.scorer/generator are replaced with
fakes before any request is made, and the client is never used as a context
manager, so the lifespan (which loads CLIP and the instruct model for real)
never runs. Behaviour of the real ClipScorer/TextGenerator belongs to a
manual check once weights can actually be downloaded, not to this suite.
"""

from __future__ import annotations

import io
import json

from fastapi.testclient import TestClient
from PIL import Image

from app.main import app
from app.scorer import InvalidImageError


class FakeScorer:
    def __init__(self, scores: list[float] | None = None, raise_invalid: bool = False):
        self._scores = scores
        self._raise_invalid = raise_invalid

    def score(self, image_bytes: bytes, prompts: list[str]) -> list[float]:
        if self._raise_invalid:
            raise InvalidImageError("bad image")
        if self._scores is not None:
            return self._scores
        return [0.5 for _ in prompts]


class FakeGenerator:
    def __init__(self, text: str | None = "generated text"):
        self._text = text

    def generate(self, prompt: str, max_tokens: int, timeout_s: int) -> str | None:
        return self._text


def _png_bytes() -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (8, 8), color=(1, 2, 3)).save(buffer, format="PNG")
    return buffer.getvalue()


def _client() -> TestClient:
    return TestClient(app)


def test_health():
    response = _client().get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_generate_returns_text():
    app.state.generator = FakeGenerator(text="hop like a frog")
    response = _client().post(
        "/generate", json={"prompt": "rewrite this", "max_tokens": 16, "timeout_s": 5}
    )
    assert response.status_code == 200
    assert response.json() == {"text": "hop like a frog"}


def test_generate_can_return_none_on_timeout():
    app.state.generator = FakeGenerator(text=None)
    response = _client().post(
        "/generate", json={"prompt": "rewrite this", "max_tokens": 16, "timeout_s": 5}
    )
    assert response.status_code == 200
    assert response.json() == {"text": None}


def test_score_returns_one_value_per_prompt():
    app.state.scorer = FakeScorer(scores=[0.9, 0.1])
    response = _client().post(
        "/score",
        files={"image": ("photo.png", _png_bytes(), "image/png")},
        data={"prompts": json.dumps(["p_play_equipment", "p_blue"])},
    )
    assert response.status_code == 200
    assert response.json() == {"scores": [0.9, 0.1]}


def test_score_rejects_malformed_prompts_json():
    app.state.scorer = FakeScorer()
    response = _client().post(
        "/score",
        files={"image": ("photo.png", _png_bytes(), "image/png")},
        data={"prompts": "not json"},
    )
    assert response.status_code == 400


def test_score_rejects_non_string_prompt_list():
    app.state.scorer = FakeScorer()
    response = _client().post(
        "/score",
        files={"image": ("photo.png", _png_bytes(), "image/png")},
        data={"prompts": json.dumps([1, 2])},
    )
    assert response.status_code == 400


def test_score_rejects_undecodable_image():
    app.state.scorer = FakeScorer(raise_invalid=True)
    response = _client().post(
        "/score",
        files={"image": ("photo.png", _png_bytes(), "image/png")},
        data={"prompts": json.dumps(["p_a"])},
    )
    assert response.status_code == 400
