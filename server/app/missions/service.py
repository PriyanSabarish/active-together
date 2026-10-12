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
from app.missions.builder import STEPS_FOR
from app.missions.generation import GENERATION_RESPONSE_SCHEMA, MAX_MISSIONS, generate_missions
from app.missions.instrumentation import RejectionStats
from app.missions.loader import load_template_dir
from app.missions.models import MissionTemplate
from app.model_client import ModelClient
from app.models import ActivityCategory, AgeBand, Context, Mission, Place, Setting

# Demo allowlist: only the families whose wording has been rewritten are
# served for now. Add an id here as each remaining family is updated; an
# empty set would serve nothing, so remove the filter below to serve all 18.
ENABLED_TEMPLATE_IDS: frozenset[str] = frozenset({
    "activity_colour_hunt",
    "activity_balance_shapes",
    "activity_follow_the_leader",
    "activity_invisible_orchestra",
    "activity_listen_and_point",
    "activity_choose_your_route",
    "activity_viewpoint_switch",
})

TEMPLATES: list[MissionTemplate] = [
    t for t in load_template_dir() if t.template_id in ENABLED_TEMPLATE_IDS
]
HOME_TEMPLATES: list[MissionTemplate] = [
    t for t in load_template_dir() if t.template_id.startswith("activity_home_")
]
ELIGIBLE_CATEGORIES: dict[str, list[str]] = load_eligible_categories()
REJECTION_STATS = RejectionStats()

_MODEL_CLIENT: ModelClient | None = (
    GeminiModelClient(
        api_key=settings.gemini_api_key,
        model=settings.gemini_model,
        response_schema=GENERATION_RESPONSE_SCHEMA,
        thinking_level=settings.gemini_thinking_level or None,
    )
    if settings.gemini_api_key and settings.mission_generation_enabled
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
    setting: Setting | str = Setting.OUTDOOR,
) -> list[Mission]:
    # If nothing is long enough for the requested bucket (the rewritten
    # families only exist at 40 minutes for now), fall back to the longest
    # shorter bucket that has missions rather than showing an empty list.
    for bucket in sorted((b for b in STEPS_FOR if b <= duration_bucket), reverse=True):
        missions = generate_missions(
            TEMPLATES,
            place,
            context,
            age_band,
            bucket,
            preferences=preferences,
            recent_template_ids=recent_template_ids,
            model_client=model_client,
            max_missions=max_missions,
            stats=REJECTION_STATS,
            eligible_categories=ELIGIBLE_CATEGORIES,
            setting=setting,
        )
        if missions:
            return missions
    return []


# At-home missions (story 9.2). There is no place and weather does not apply
# (D23), so the selector gets a placeholder place and an unavailable context;
# the home templates are category "any", so neither is read for matching.
_HOME_PLACE = Place(
    place_id="home",
    display_name="Home",
    activity_category=ActivityCategory.PLAYGROUND,
    lga_name="",
    latitude=0.0,
    longitude=0.0,
    distance_m=0,
    classification_confidence=0.0,
)
_NO_WEATHER = Context(available=False)


def home_bucket(total_min: int) -> int:
    """Plan length for a home session: the largest of 20/40/60 that fits, and 20
    for anything shorter (the minimum for home is still an open item)."""
    return max((b for b in STEPS_FOR if b <= total_min), default=min(STEPS_FOR))


def get_home_missions(
    age_band: AgeBand,
    total_min: int,
    recent_template_ids: Iterable[str] = (),
    max_missions: int = MAX_MISSIONS,
) -> list[Mission]:
    """2-3 at-home missions through the same selection, build and validation path
    as outdoor ones, with the two home safety rules applied. Library wording
    only: the model prompt describes a place and the weather, neither of which
    exists at home, so no rewrite is requested and nothing waits on a model."""
    for bucket in sorted((b for b in STEPS_FOR if b <= home_bucket(total_min)), reverse=True):
        missions = generate_missions(
            HOME_TEMPLATES,
            _HOME_PLACE,
            _NO_WEATHER,
            age_band,
            bucket,
            recent_template_ids=recent_template_ids,
            model_client=None,
            max_missions=max_missions,
            stats=REJECTION_STATS,
            setting=Setting.HOME,
        )
        if missions:
            return missions
    return []
