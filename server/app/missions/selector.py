"""
select_templates (B20) — the first filter stage inside generate_missions.

Six hard pass/fail dimensions: category, weather tag, age band, bucket,
preference exclusion, recent history. No ranking and no relaxation here —
if excluding every preferred-away category or every recently-served
template empties the result, that's B28's relaxation rule and B33's
recency weighting to handle, not this function's.

templates is accepted as a plain argument (not loaded internally) so this
stays testable with fixtures, matching every other pure function in
Backend B — generate_missions (B23) is what will pass it the real,
reviewed library.
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
) -> list[MissionTemplate]:
    if duration_bucket not in STEPS_FOR:
        raise ValueError(f"duration_bucket must be one of {sorted(STEPS_FOR)}, got {duration_bucket}")

    excluded_categories = frozenset(preferences)
    excluded_ids = frozenset(recent_template_ids)
    applicable_tags = classify_weather_tags(context)

    return [
        template
        for template in templates
        if _matches_category(template, place)
        and _matches_weather(template, applicable_tags)
        and age_band in template.bands
        and template.duration_bucket >= duration_bucket
        and template.category not in excluded_categories
        and template.template_id not in excluded_ids
    ]


def _matches_category(template: MissionTemplate, place: Place) -> bool:
    return template.category == "any" or template.category == place.activity_category.value


def _matches_weather(template: MissionTemplate, applicable_tags: frozenset) -> bool:
    return any(tag in applicable_tags for tag in template.weather_tags)
