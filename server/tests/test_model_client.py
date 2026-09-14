from __future__ import annotations

from app.model_client import FixtureModelClient, ModelClient


def test_fixture_satisfies_the_protocol():
    client: ModelClient = FixtureModelClient()
    assert isinstance(client, ModelClient)


def test_default_text_response():
    client = FixtureModelClient(default_text="hello")
    assert client.generate_text("any prompt", max_tokens=32, timeout_s=5) == "hello"


def test_text_response_overridden_per_prompt():
    client = FixtureModelClient(text_responses={"greet": "hi there"}, default_text="fallback")
    assert client.generate_text("greet", max_tokens=32, timeout_s=5) == "hi there"
    assert client.generate_text("other", max_tokens=32, timeout_s=5) == "fallback"


def test_generate_text_can_return_none():
    client = FixtureModelClient(default_text=None)
    assert client.generate_text("any prompt", max_tokens=32, timeout_s=5) is None
