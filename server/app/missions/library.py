"""
serve_from_library (B24) — the guaranteed, no-model path generate_missions
(B23) will fall back to when generation fails, times out, or every
candidate is rejected. Built first, so generation becomes an improvement
rather than a dependency: story 5.1's five-second budget is satisfied by
this path alone, since it never makes a network call.

Tries eligible templates in order, skipping any that fail validation —
"a rejected mission is never shown to a user; a different template is
served instead" (content/schema/safety_constraints.yaml's own enforcement
rule) — and returns the first one that passes both the schema validator
(B21) and the safety validator (B22). None means no eligible template
survived; generate_missions (B23) owns the further guarantee that it
"always returns something," not this function.

No ranking happens here beyond select_templates' own filtering order —
there's no dedicated template-ranking task in this iteration's plan, so
candidates are tried in the order they're given.
"""

from __future__ import annotations

from typing import Iterable

from app.missions.builder import build_mission
from app.missions.models import MissionTemplate
from app.missions.safety import validate_mission
from app.missions.schema_validator import validate_schema
from app.missions.selector import select_templates
from app.models import AgeBand, Context, Mission, Place


def serve_from_library(
    templates: Iterable[MissionTemplate],
    place: Place,
    context: Context,
    age_band: AgeBand,
    duration_bucket: int,
    preferences: Iterable[str] = (),
    recent_template_ids: Iterable[str] = (),
    eligible_categories: dict[str, list[str]] | None = None,
) -> Mission | None:
    candidates = select_templates(
        templates, place, context, age_band, duration_bucket, preferences, recent_template_ids,
        eligible_categories=eligible_categories,
    )

    for template in candidates:
        if not validate_schema(template).ok:
            continue

        mission = build_mission(template, age_band, duration_bucket)

        if not validate_mission(mission, template).ok:
            continue

        return mission

    return None
