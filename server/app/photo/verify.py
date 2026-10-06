"""verify_step() — Backend B's side of POST /verify-step (B55).

    verify_step(image_bytes, prompt_id, attempt) -> Verification

Scorer order is hosted first (when configured and healthy), then the API,
then use_tap. By default a scorer is only asked about prompts that were
measured and kept for that scorer (B54); a prompt kept for the hosted scorer
only is never sent to the API while the host is down. PHOTO_REQUIRE_MEASURED=false
switches that gate off: candidate prompts are asked too, dropped ones still
are not. The hosted scorer still needs a measured threshold, so unmeasured
prompts reach only the API.

Attempts: three in total. A "no match" on attempts 1 and 2 returns retry; on
attempt 3 it returns use_tap. When no scorer can answer, the result is
use_tap at once, whatever the attempt number, so a child is never made to
retake photos that nothing is able to check.

The image stays in memory. This module never logs it or writes it anywhere.
"""

from __future__ import annotations

from typing import Sequence

from app.config import settings
from app.photo.models import MAX_ATTEMPTS, Prompt, ScorerUnavailable, Verification
from app.photo.scorers import ApiImageScorer, HostedImageScorer, ImageScorer
from app.photo.vocabulary import load_vocabulary

_USE_TAP_NOW = Verification(result="use_tap", attempts_left=0, checked_by=None)

_default_scorers: list[ImageScorer] | None = None
_default_vocabulary: dict[str, Prompt] | None = None


def build_scorers() -> list[ImageScorer]:
    """The configured chain, in order: hosted, then api."""
    api_client = None
    if settings.gemini_api_key:
        from app.gemini_client import GeminiModelClient

        api_client = GeminiModelClient(api_key=settings.gemini_api_key, model=settings.gemini_model)
    return [
        HostedImageScorer(
            settings.inference_host_url,
            settings.inference_host_token,
            timeout_s=settings.photo_check_timeout_s,
        ),
        ApiImageScorer(
            api_client,
            enabled=settings.photo_api_enabled,
            timeout_s=int(settings.photo_check_timeout_s),
        ),
    ]


def _may_ask(prompt: Prompt, scorer_name: str, require_measured: bool) -> bool:
    """Kept for this scorer, or, with the gate off, anything not dropped for it."""
    if prompt.kept_for(scorer_name):
        return True
    if require_measured:
        return False
    status = prompt.scorers.get(scorer_name)
    return status is None or status.status != "dropped"


def verify_step(
    image_bytes: bytes,
    prompt_id: str,
    attempt: int,
    scorers: Sequence[ImageScorer] | None = None,
    vocabulary: dict[str, Prompt] | None = None,
    require_measured: bool | None = None,
) -> Verification:
    global _default_scorers, _default_vocabulary

    if isinstance(attempt, bool) or not isinstance(attempt, int) or not 1 <= attempt <= MAX_ATTEMPTS:
        raise ValueError(f"attempt must be an integer from 1 to {MAX_ATTEMPTS}, got {attempt!r}")

    if scorers is None:
        if _default_scorers is None:
            _default_scorers = build_scorers()
        scorers = _default_scorers
    if vocabulary is None:
        if _default_vocabulary is None:
            _default_vocabulary = load_vocabulary()
        vocabulary = _default_vocabulary

    if require_measured is None:
        require_measured = settings.photo_require_measured

    prompt = vocabulary.get(prompt_id)
    if prompt is None:
        return _USE_TAP_NOW

    for scorer in scorers:
        if not _may_ask(prompt, scorer.name, require_measured) or not scorer.available():
            continue
        try:
            matched = scorer.check(image_bytes, prompt)
        except ScorerUnavailable:
            continue
        if matched:
            return Verification("confirmed", MAX_ATTEMPTS - attempt, scorer.name)
        if attempt < MAX_ATTEMPTS:
            return Verification("retry", MAX_ATTEMPTS - attempt, scorer.name)
        return Verification("use_tap", 0, scorer.name)

    return _USE_TAP_NOW
