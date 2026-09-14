"""
ModelClient — the seam between Backend B's model-shaped logic and whatever
actually generates text.

Selection, validation, threshold and retry logic in app.recommendation and
app.missions is written against this interface, never against a live
provider. FixtureModelClient makes all of that testable with no model
running; GeminiModelClient (B37) is this iteration's real implementation.
A HostedModelClient talking to a self-hosted inference service comes later,
when photo verification (deferred to the end of this iteration) adds
score_image to this interface — it isn't here yet because nothing needs it
yet.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class ModelClient(Protocol):
    def generate_text(self, prompt: str, max_tokens: int, timeout_s: int) -> str | None:
        """Return generated text, or None on failure or timeout."""
        ...


class FixtureModelClient:
    """Deterministic ModelClient used by every test in Backend B.

    No network call, no timing behaviour: generate_text returns a canned
    value so selection, validation and retry tests never depend on a
    running model or a provider key.
    """

    def __init__(
        self,
        text_responses: dict[str, str] | None = None,
        default_text: str | None = "fixture response",
    ) -> None:
        self._text_responses = text_responses or {}
        self._default_text = default_text

    def generate_text(self, prompt: str, max_tokens: int, timeout_s: int) -> str | None:
        return self._text_responses.get(prompt, self._default_text)
