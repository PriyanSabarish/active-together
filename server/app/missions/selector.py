"""
select_templates (B20, B33) — the first filter stage inside generate_missions.

Four hard pass/fail dimensions — category, weather tag, age band, bucket —
that never relax: a template either fits the request or it doesn't. Two
soft exclusion dimensions, applied on top and each relaxing independently
back to its own input if it would empty the result: preference exclusion
(a category the family wants to avoid) and recent-history exclusion (B33
— don't serve the same template twice in a row). Getting nothing because
the family has played through the whole eligible library recently is a
worse experience than an occasional repeat, so recency loses to "return
something" exactly the way preference already does.

Category matching: every template in the real reviewed library uses
category "any" — the actual per-place-type shortlist lives in the separate
content/taxonomy/mission_context_bindings.yaml (eligible_categories here,
keyed by template_id). A template with no entry, or an explicit non-"any"
category, falls back to the older direct-match rule. A template with no
binding at all is treated as unbound, matching everywhere, rather than
silently excluded — nobody has categorised it yet, which isn't the same as
it being unsuitable everywhere.

templates is accepted as a plain argument (not loaded internally) so this
stays testable with fixtures, matching every other pure function in
Backend B — generate_missions (B23) is what will pass it the real,
reviewed library. eligible_categories works the same way.
"""

from __future__ import annotations

from typing import Iterable

from app.missions.builder import STEPS_FOR
from app.missions.models import MissionTemplate
from app.missions.weather_tags import classify_weather_tags
from app.models import AgeBand, Context, Place


def select_templates(
    templates: Iterable[MissionTemplate],
    place: Place,
    context: Context,
    age_band: AgeBand,
    duration_bucket: int,
    preferences: Iterable[str] = (),
    recent_template_ids: Iterable[str] = (),
    eligible_categories: dict[str, list[str]] | None = None,
) -> list[MissionTemplate]:
    if duration_bucket not in STEPS_FOR:
        raise ValueError(f"duration_bucket must be one of {sorted(STEPS_FOR)}, got {duration_bucket}")

    excluded_categories = frozenset(preferences)
    excluded_ids = frozenset(recent_template_ids)
    applicable_tags = classify_weather_tags(context)
    eligible_categories = eligible_categories or {}

    eligible = [
        template
        for template in templates
        if _matches_category(template, place, eligible_categories)
        and _matches_weather(template, applicable_tags)
        and age_band in template.bands
        and template.duration_bucket >= duration_bucket
    ]

    after_preferences = [t for t in eligible if t.category not in excluded_categories]
    if not after_preferences:
        after_preferences = eligible

    after_recent = [t for t in after_preferences if t.template_id not in excluded_ids]
    if not after_recent:
        after_recent = after_preferences

    return after_recent


def _matches_category(
    template: MissionTemplate, place: Place, eligible_categories: dict[str, list[str]]
) -> bool:
    if template.category != "any":
        return template.category == place.activity_category.value

    bound = eligible_categories.get(template.template_id)
    if not bound:
        return True

    return place.activity_category.value in bound


def _matches_weather(template: MissionTemplate, applicable_tags: frozenset) -> bool:
    return any(tag in applicable_tags for tag in template.weather_tags)
