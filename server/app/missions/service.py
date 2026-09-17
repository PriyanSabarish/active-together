"""
Integration surface for Backend A — the one function to call (B23 wiring).

Loads the real reviewed library, the real category bindings, and
constructs the Gemini model client ONCE at import time, so a request
handler doesn't repeat that work per call. get_missions' parameter list
is exactly section 1.2's agreed generate_missions signature (place,
context, age_band, duration_bucket, preferences, recent_template_ids)
plus max_missions — nothing about templates, model clients, or bindings
crosses the seam.

Resolving whatever Backend A's request shape uses (combo_id, etc.) into a
real Place and Context is Backend A's job, per the agreed split — this
function starts from Place/Context, not before them.

get_missions is a plain, synchronous, blocking call (GeminiModelClient
makes a real HTTP request under the hood) — call it from inside
asyncio.to_thread(...), never awaited directly from an async def, or it
blocks the event loop for the length of the Gemini call.

model_client defaults to None (skipping generation, pure library-direct)
whenever GEMINI_API_KEY isn't configured, so this module still imports
and works with no key set — and tests can pass model_client=None or a
FixtureModelClient explicitly to avoid ever calling the real API.
"""

from __future__ import annotations

from typing import Iterable

from app.config import settings
from app.gemini_client import GeminiModelClient
from app.missions.context_bindings import load_eligible_categories
from app.missions.generation import GENERATION_RESPONSE_SCHEMA, MAX_MISSIONS, generate_missions
from app.missions.instrumentation import RejectionStats
from app.missions.loader import load_template_dir
from app.missions.models import MissionTemplate
from app.model_client import ModelClient
from app.models import AgeBand, Context, Mission, Place

TEMPLATES: list[MissionTemplate] = load_template_dir()
ELIGIBLE_CATEGORIES: dict[str, list[str]] = load_eligible_categories()
REJECTION_STATS = RejectionStats()

_MODEL_CLIENT: ModelClient | None = (
    GeminiModelClient(
        api_key=settings.gemini_api_key,
        model=settings.gemini_model,
        response_schema=GENERATION_RESPONSE_SCHEMA,
    )
    if settings.gemini_api_key
    else None
)


def get_missions(
    place: Place,
    context: Context,
    age_band: AgeBand,
    duration_bucket: int,
    preferences: Iterable[str] = (),
    recent_template_ids: Iterable[str] = (),
    max_missions: int = MAX_MISSIONS,
    model_client: ModelClient | None = _MODEL_CLIENT,
) -> list[Mission]:
    return generate_missions(
        TEMPLATES,
        place,
        context,
        age_band,
        duration_bucket,
        preferences=preferences,
        recent_template_ids=recent_template_ids,
        model_client=model_client,
        max_missions=max_missions,
        stats=REJECTION_STATS,
        eligible_categories=ELIGIBLE_CATEGORIES,
    )
