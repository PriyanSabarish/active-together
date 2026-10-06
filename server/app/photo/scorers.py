"""ImageScorer chain members (B51-B53).

    class ImageScorer:
        name: str
        def available(self) -> bool
        def check(self, image_bytes, prompt) -> bool

check() returns True when the photo matches the prompt and False when it does
not. A scorer that cannot answer at all raises ScorerUnavailable, which is not
the same thing as False.

No scorer writes image bytes anywhere or logs them. Failures are logged by
exception class or status code only.
"""

from __future__ import annotations

import json
import logging
import time
from typing import Callable, Protocol, runtime_checkable

import httpx

from app.photo.models import Prompt, ScorerUnavailable

logger = logging.getLogger(__name__)

API = "api"
OWN_HOST = "own_host"


@runtime_checkable
class ImageScorer(Protocol):
    name: str

    def available(self) -> bool: ...

    def check(self, image_bytes: bytes, prompt: Prompt) -> bool: ...


class FixtureImageScorer:
    """Deterministic scorer for tests: no network, no model.

    answers maps prompt id -> bool. A prompt id missing from answers uses
    default. With fail=True every check raises ScorerUnavailable, to model a
    scorer that is configured but unreachable.
    """

    def __init__(
        self,
        name: str = API,
        answers: dict[str, bool] | None = None,
        default: bool = True,
        is_available: bool = True,
        fail: bool = False,
    ) -> None:
        self.name = name
        self._answers = answers or {}
        self._default = default
        self._available = is_available
        self._fail = fail
        self.calls: list[str] = []

    def available(self) -> bool:
        return self._available

    def check(self, image_bytes: bytes, prompt: Prompt) -> bool:
        self.calls.append(prompt.id)
        if self._fail:
            raise ScorerUnavailable("fixture scorer set to fail")
        return self._answers.get(prompt.id, self._default)


# Api (Gemini multimodal)

MATCH_SCHEMA = {
    "type": "OBJECT",
    "properties": {"match": {"type": "BOOLEAN"}},
    "required": ["match"],
}


def build_api_question(prompt_text: str) -> str:
    return (
        f'Does this photo clearly show "{prompt_text}"? '
        'Answer with JSON only: {"match": true} or {"match": false}. '
        "If the photo is unclear, blurry or you are unsure, answer false."
    )


class ApiImageScorer:
    """Gemini multimodal call with a fixed JSON answer and temperature 0.

    enabled is the switch for mentor sign-off on sending photo-check images to
    a third party (decision D6) and the Gemini data terms (D2). Until it is
    switched on this scorer reports unavailable and nothing is ever sent.
    """

    name = API

    def __init__(self, client, enabled: bool = False, timeout_s: int = 8, max_tokens: int = 32) -> None:
        self._client = client
        self._enabled = enabled
        self._timeout_s = timeout_s
        self._max_tokens = max_tokens

    def available(self) -> bool:
        return self._enabled and self._client is not None

    def check(self, image_bytes: bytes, prompt: Prompt) -> bool:
        if not self.available():
            raise ScorerUnavailable("api scorer is not enabled")
        text = self._client.generate_from_image(
            build_api_question(prompt.text),
            image_bytes,
            max_tokens=self._max_tokens,
            timeout_s=self._timeout_s,
            response_schema=MATCH_SCHEMA,
        )
        if text is None:
            raise ScorerUnavailable("api returned nothing")
        try:
            match = json.loads(text)["match"]
        except (ValueError, KeyError, TypeError) as exc:
            raise ScorerUnavailable("api reply was not the fixed JSON answer") from exc
        if not isinstance(match, bool):
            raise ScorerUnavailable("api reply was not the fixed JSON answer")
        return match


# Hosted (own inference host)


class HostedImageScorer:
    """Calls the host's scoring route and applies the prompt's own threshold.

    The threshold comes from vocabulary.yaml (measured per prompt by B54), so
    this class never carries a number of its own. Available only when a URL
    and token are configured and the host answers its health check; the health
    result is cached briefly so a down host does not add a timeout to every
    photo.
    """

    name = OWN_HOST
    HEALTH_TTL_S = 30.0

    def __init__(
        self,
        base_url: str | None,
        token: str | None,
        timeout_s: float = 8.0,
        health_timeout_s: float = 2.0,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._base_url = base_url.rstrip("/") if base_url else None
        self._token = token
        self._timeout_s = timeout_s
        self._health_timeout_s = health_timeout_s
        self._clock = clock
        self._healthy_until = 0.0
        self._unhealthy_until = 0.0

    @property
    def configured(self) -> bool:
        return bool(self._base_url and self._token)

    def available(self) -> bool:
        if not self.configured:
            return False
        now = self._clock()
        if now < self._healthy_until:
            return True
        if now < self._unhealthy_until:
            return False
        try:
            response = httpx.get(f"{self._base_url}/health", timeout=self._health_timeout_s)
            healthy = response.status_code == 200
        except httpx.HTTPError as exc:
            logger.warning("Inference host health check failed: %s", type(exc).__name__)
            healthy = False
        if healthy:
            self._healthy_until = now + self.HEALTH_TTL_S
        else:
            self._unhealthy_until = now + self.HEALTH_TTL_S
        return healthy

    def check(self, image_bytes: bytes, prompt: Prompt) -> bool:
        status = prompt.scorers.get(self.name)
        if status is None or status.threshold is None:
            raise ScorerUnavailable("no measured threshold for this prompt")
        return self.score(image_bytes, prompt.text) >= status.threshold

    def score(self, image_bytes: bytes, prompt_text: str) -> float:
        """Raw similarity from the host. B54 uses this to fit thresholds."""
        if not self.configured:
            raise ScorerUnavailable("hosted scorer is not configured")
        try:
            # Raw body, not multipart: the host reads it straight into memory.
            response = httpx.post(
                f"{self._base_url}/score",
                params={"prompt": prompt_text},
                headers={"Authorization": f"Bearer {self._token}", "Content-Type": "image/jpeg"},
                content=image_bytes,
                timeout=self._timeout_s,
            )
        except httpx.HTTPError as exc:
            self._mark_down()
            logger.warning("Inference host request failed: %s", type(exc).__name__)
            raise ScorerUnavailable("host unreachable") from exc
        if response.status_code != 200:
            self._mark_down()
            logger.warning("Inference host returned %s", response.status_code)
            raise ScorerUnavailable(f"host returned {response.status_code}")
        try:
            return float(response.json()["score"])
        except (ValueError, KeyError, TypeError) as exc:
            raise ScorerUnavailable("host reply had no score") from exc

    def _mark_down(self) -> None:
        self._healthy_until = 0.0
        self._unhealthy_until = self._clock() + self.HEALTH_TTL_S
