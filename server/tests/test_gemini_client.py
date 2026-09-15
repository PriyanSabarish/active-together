from __future__ import annotations

import json

import httpx
import pytest

from app.gemini_client import GeminiModelClient
from app.model_client import ModelClient


class FakeResponse:
    def __init__(self, status_code: int, payload: dict | None = None, text: str = ""):
        self.status_code = status_code
        self._payload = payload
        self.text = text

    def json(self):
        if self._payload is None:
            raise ValueError("no JSON body")
        return self._payload


def _gemini_payload(text: str) -> dict:
    return {"candidates": [{"content": {"parts": [{"text": text}]}}]}


def test_satisfies_the_modelclient_protocol():
    client: ModelClient = GeminiModelClient(api_key="fake-key")
    assert isinstance(client, ModelClient)


def test_successful_generation_returns_text(monkeypatch):
    monkeypatch.setattr(httpx, "post", lambda *a, **kw: FakeResponse(200, _gemini_payload("hop like a frog")))
    client = GeminiModelClient(api_key="fake-key")
    assert client.generate_text("rewrite this", max_tokens=32, timeout_s=5) == "hop like a frog"


def test_non_200_status_returns_none(monkeypatch):
    monkeypatch.setattr(httpx, "post", lambda *a, **kw: FakeResponse(500, text="server error"))
    client = GeminiModelClient(api_key="fake-key")
    assert client.generate_text("rewrite this", max_tokens=32, timeout_s=5) is None


def test_malformed_response_returns_none(monkeypatch):
    monkeypatch.setattr(httpx, "post", lambda *a, **kw: FakeResponse(200, payload={"unexpected": "shape"}))
    client = GeminiModelClient(api_key="fake-key")
    assert client.generate_text("rewrite this", max_tokens=32, timeout_s=5) is None


def test_empty_candidates_returns_none(monkeypatch):
    monkeypatch.setattr(httpx, "post", lambda *a, **kw: FakeResponse(200, payload={"candidates": []}))
    client = GeminiModelClient(api_key="fake-key")
    assert client.generate_text("rewrite this", max_tokens=32, timeout_s=5) is None


def test_non_json_body_returns_none(monkeypatch):
    monkeypatch.setattr(httpx, "post", lambda *a, **kw: FakeResponse(200, payload=None))
    client = GeminiModelClient(api_key="fake-key")
    assert client.generate_text("rewrite this", max_tokens=32, timeout_s=5) is None


@pytest.mark.parametrize("exc", [httpx.ConnectError("boom"), httpx.TimeoutException("timed out")])
def test_network_errors_return_none(monkeypatch, exc):
    def _raise(*args, **kwargs):
        raise exc

    monkeypatch.setattr(httpx, "post", _raise)
    client = GeminiModelClient(api_key="fake-key")
    assert client.generate_text("rewrite this", max_tokens=32, timeout_s=5) is None


def test_request_uses_expected_url_params_and_timeout(monkeypatch):
    captured = {}

    def _fake_post(url, params=None, json=None, timeout=None):
        captured["url"] = url
        captured["params"] = params
        captured["json"] = json
        captured["timeout"] = timeout
        return FakeResponse(200, _gemini_payload("ok"))

    monkeypatch.setattr(httpx, "post", _fake_post)
    client = GeminiModelClient(api_key="secret-key", model="gemini-2.0-flash")
    client.generate_text("hello", max_tokens=64, timeout_s=7)

    assert captured["url"] == "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
    assert captured["params"] == {"key": "secret-key"}
    assert captured["json"]["contents"] == [{"parts": [{"text": "hello"}]}]
    assert captured["json"]["generationConfig"]["maxOutputTokens"] == 64
    assert captured["timeout"] == 7


def test_custom_model_and_base_url_are_used(monkeypatch):
    captured = {}
    monkeypatch.setattr(httpx, "post", lambda url, **kw: (captured.setdefault("url", url), FakeResponse(200, _gemini_payload("ok")))[1])

    client = GeminiModelClient(api_key="k", model="gemini-custom", base_url="https://example.test/v1")
    client.generate_text("hi", max_tokens=10, timeout_s=5)

    assert captured["url"] == "https://example.test/v1/models/gemini-custom:generateContent"


def test_no_response_schema_by_default(monkeypatch):
    captured = {}

    def _fake_post(url, params=None, json=None, timeout=None):
        captured["generation_config"] = json["generationConfig"]
        return FakeResponse(200, _gemini_payload("ok"))

    monkeypatch.setattr(httpx, "post", _fake_post)
    GeminiModelClient(api_key="k").generate_text("hi", max_tokens=10, timeout_s=5)

    assert "responseMimeType" not in captured["generation_config"]
    assert "responseSchema" not in captured["generation_config"]


def test_response_schema_is_included_when_set(monkeypatch):
    schema = {"type": "OBJECT", "properties": {"steps": {"type": "ARRAY", "items": {"type": "STRING"}}}}
    captured = {}

    def _fake_post(url, params=None, json=None, timeout=None):
        captured["generation_config"] = json["generationConfig"]
        return FakeResponse(200, _gemini_payload('{"steps": ["a", "b"]}'))

    monkeypatch.setattr(httpx, "post", _fake_post)
    client = GeminiModelClient(api_key="k", response_schema=schema)
    client.generate_text("hi", max_tokens=10, timeout_s=5)

    assert captured["generation_config"]["responseMimeType"] == "application/json"
    assert captured["generation_config"]["responseSchema"] == schema


def test_structured_output_parses_with_plain_json_loads(monkeypatch):
    schema = {"type": "OBJECT", "properties": {"steps": {"type": "ARRAY", "items": {"type": "STRING"}}}}
    monkeypatch.setattr(
        httpx, "post",
        lambda *a, **kw: FakeResponse(200, _gemini_payload('{"steps": ["Hop to the fence.", "Wave both arms."]}')),
    )

    client = GeminiModelClient(api_key="k", response_schema=schema)
    text = client.generate_text("hi", max_tokens=64, timeout_s=5)

    parsed = json.loads(text)
    assert parsed == {"steps": ["Hop to the fence.", "Wave both arms."]}
