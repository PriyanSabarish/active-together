"""ApiImageScorer, HostedImageScorer and the multimodal Gemini call (B52, B53)."""

from __future__ import annotations

import base64
import logging

import httpx
import pytest

from app.gemini_client import GeminiModelClient
from app.photo.models import Prompt, ScorerStatus, ScorerUnavailable
from app.photo.scorers import (
    ApiImageScorer,
    HostedImageScorer,
    ImageScorer,
    build_api_question,
)

IMAGE = b"\xff\xd8secret-photo-bytes"
PROMPT = Prompt("p_red", "something red", {"own_host": ScorerStatus("kept", threshold=0.30)})


class FakeResponse:
    def __init__(self, status_code=200, payload=None, text=""):
        self.status_code = status_code
        self._payload = payload
        self.text = text

    def json(self):
        if self._payload is None:
            raise ValueError("no json")
        return self._payload


class StubImageClient:
    def __init__(self, reply):
        self.reply = reply
        self.calls = []

    def generate_from_image(self, prompt, image_bytes, **kwargs):
        self.calls.append((prompt, image_bytes, kwargs))
        return self.reply


# Gemini multimodal call


def test_generate_from_image_sends_inline_image_at_temperature_zero(monkeypatch):
    seen = {}

    def fake_post(url, params=None, json=None, timeout=None):
        seen.update(url=url, json=json, timeout=timeout)
        return FakeResponse(200, {"candidates": [{"content": {"parts": [{"text": '{"match": true}'}]}}]})

    monkeypatch.setattr(httpx, "post", fake_post)
    client = GeminiModelClient(api_key="k")
    out = client.generate_from_image("q?", IMAGE, max_tokens=16, timeout_s=4, response_schema={"type": "OBJECT"})
    assert out == '{"match": true}'
    parts = seen["json"]["contents"][0]["parts"]
    assert parts[0] == {"text": "q?"}
    assert base64.b64decode(parts[1]["inline_data"]["data"]) == IMAGE
    config = seen["json"]["generationConfig"]
    assert config["temperature"] == 0
    assert config["responseMimeType"] == "application/json"
    assert seen["timeout"] == 4


def test_generate_from_image_failure_returns_none_and_logs_no_image(monkeypatch, caplog):
    def boom(*a, **kw):
        raise httpx.ConnectError("down")

    monkeypatch.setattr(httpx, "post", boom)
    with caplog.at_level(logging.DEBUG):
        assert GeminiModelClient(api_key="k").generate_from_image("q", IMAGE, 16, 4) is None
    logged = caplog.text
    assert base64.b64encode(IMAGE).decode() not in logged
    assert "secret-photo-bytes" not in logged


# ApiImageScorer


def test_api_scorer_is_unavailable_until_enabled_and_never_calls_the_client():
    client = StubImageClient('{"match": true}')
    scorer = ApiImageScorer(client, enabled=False)
    assert scorer.available() is False
    with pytest.raises(ScorerUnavailable):
        scorer.check(IMAGE, PROMPT)
    assert client.calls == []


def test_api_scorer_needs_a_client():
    assert ApiImageScorer(None, enabled=True).available() is False


@pytest.mark.parametrize(("reply", "expected"), [('{"match": true}', True), ('{"match": false}', False)])
def test_api_scorer_reads_the_fixed_answer(reply, expected):
    client = StubImageClient(reply)
    scorer = ApiImageScorer(client, enabled=True)
    assert isinstance(scorer, ImageScorer)
    assert scorer.check(IMAGE, PROMPT) is expected
    question, image, kwargs = client.calls[0]
    assert "something red" in question
    assert image == IMAGE
    assert kwargs["response_schema"]["required"] == ["match"]


@pytest.mark.parametrize("reply", [None, "", "yes", "{}", '{"match": "true"}', '{"match": 1}', "[true]"])
def test_api_scorer_treats_anything_else_as_unavailable_not_as_no(reply):
    scorer = ApiImageScorer(StubImageClient(reply), enabled=True)
    with pytest.raises(ScorerUnavailable):
        scorer.check(IMAGE, PROMPT)


def test_question_tells_the_model_to_say_false_when_unsure():
    assert "unsure" in build_api_question("a leaf")
    assert '"a leaf"' in build_api_question("a leaf")


# HostedImageScorer


class Clock:
    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now


def test_hosted_scorer_is_unavailable_without_url_and_token(monkeypatch):
    monkeypatch.setattr(httpx, "get", lambda *a, **kw: pytest.fail("must not call the network"))
    assert HostedImageScorer(None, "t").available() is False
    assert HostedImageScorer("https://h", None).available() is False
    assert HostedImageScorer("", "").available() is False


def test_hosted_health_is_cached_and_reflects_the_host(monkeypatch):
    clock = Clock()
    calls = []
    status = {"code": 200}

    def fake_get(url, timeout=None):
        calls.append(url)
        return FakeResponse(status["code"])

    monkeypatch.setattr(httpx, "get", fake_get)
    scorer = HostedImageScorer("https://host/", "tok", clock=clock)
    assert scorer.available() is True
    assert scorer.available() is True
    assert calls == ["https://host/health"]  # cached, trailing slash handled
    clock.now += HostedImageScorer.HEALTH_TTL_S + 1
    status["code"] = 503
    assert scorer.available() is False
    assert scorer.available() is False
    assert len(calls) == 2  # unhealthy result cached too


def test_hosted_health_unreachable_is_unavailable(monkeypatch):
    def boom(*a, **kw):
        raise httpx.ConnectError("down")

    monkeypatch.setattr(httpx, "get", boom)
    assert HostedImageScorer("https://h", "t", clock=Clock()).available() is False


def test_hosted_check_applies_the_per_prompt_threshold_and_sends_the_token(monkeypatch):
    seen = {}

    def fake_post(url, params=None, headers=None, content=None, timeout=None):
        seen.update(url=url, params=params, headers=headers, content=content)
        return FakeResponse(200, {"score": seen_score["v"]})

    seen_score = {"v": 0.31}
    monkeypatch.setattr(httpx, "post", fake_post)
    scorer = HostedImageScorer("https://host", "tok")
    assert scorer.check(IMAGE, PROMPT) is True  # 0.31 >= 0.30
    seen_score["v"] = 0.30
    assert scorer.check(IMAGE, PROMPT) is True  # exactly at threshold
    seen_score["v"] = 0.2999
    assert scorer.check(IMAGE, PROMPT) is False
    assert seen["url"] == "https://host/score"
    assert seen["headers"]["Authorization"] == "Bearer tok"
    assert seen["params"] == {"prompt": "something red"}
    assert seen["content"] == IMAGE  # raw body, never multipart


def test_hosted_check_without_a_threshold_is_unavailable_and_sends_nothing(monkeypatch):
    monkeypatch.setattr(httpx, "post", lambda *a, **kw: pytest.fail("must not send"))
    bare = Prompt("p_red", "something red", {"own_host": ScorerStatus("kept")})
    with pytest.raises(ScorerUnavailable):
        HostedImageScorer("https://host", "tok").check(IMAGE, bare)
    with pytest.raises(ScorerUnavailable):
        HostedImageScorer("https://host", "tok").check(IMAGE, Prompt("p_red", "x"))


@pytest.mark.parametrize(
    "response",
    [FakeResponse(500), FakeResponse(401), FakeResponse(200, None), FakeResponse(200, {}), FakeResponse(200, {"score": None}), FakeResponse(200, {"scores": [0.4]})],
)
def test_hosted_bad_replies_are_unavailable(monkeypatch, response):
    monkeypatch.setattr(httpx, "post", lambda *a, **kw: response)
    with pytest.raises(ScorerUnavailable):
        HostedImageScorer("https://host", "tok").check(IMAGE, PROMPT)


def test_hosted_timeout_is_unavailable_and_marks_the_host_down(monkeypatch, caplog):
    def boom(*a, **kw):
        raise httpx.ReadTimeout("slow")

    monkeypatch.setattr(httpx, "post", boom)
    monkeypatch.setattr(httpx, "get", lambda *a, **kw: pytest.fail("down host should not be probed again"))
    scorer = HostedImageScorer("https://host", "tok", clock=Clock())
    with caplog.at_level(logging.DEBUG):
        with pytest.raises(ScorerUnavailable):
            scorer.check(IMAGE, PROMPT)
    assert scorer.available() is False
    assert "secret-photo-bytes" not in caplog.text


def test_generate_from_image_sends_the_photo_thinking_level_when_set(monkeypatch):
    seen = {}

    def fake_post(url, params=None, json=None, timeout=None):
        seen.update(json=json)
        return FakeResponse(200, {"candidates": [{"content": {"parts": [{"text": "{}"}]}}]})

    monkeypatch.setattr(httpx, "post", fake_post)
    GeminiModelClient(api_key="k", photo_thinking_level="minimal").generate_from_image("q", IMAGE, 16, 4)
    assert seen["json"]["generationConfig"]["thinkingConfig"] == {"thinkingLevel": "minimal"}
    GeminiModelClient(api_key="k").generate_from_image("q", IMAGE, 16, 4)
    assert "thinkingConfig" not in seen["json"]["generationConfig"]
