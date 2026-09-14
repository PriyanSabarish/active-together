"""
build_mission (B29) — band selection and truncation to 3, 5 or 7 steps.

A template holds up to seven steps per band, sized for the family's longest
covered duration_bucket. A 40-minute mission is the first five of those
steps and a 20-minute mission is the first three — truncation happens once,
here, so neither the client nor the generator has to know the rule.

Step keeps verify_mode and prompt_id from the authored TemplateStep
unchanged even though every step served this iteration is "self" in
practice — no coercion happens here. Whether a "photo" step should ever
reach this function is a content-library question (see the open item on
which library the app serves), not something build_mission decides.
"""

from __future__ import annotations

import uuid

from app.missions.models import MissionTemplate
from app.models import AgeBand, Mission, Step

STEPS_FOR: dict[int, int] = {20: 3, 40: 5, 60: 7}


def build_mission(template: MissionTemplate, band: AgeBand, duration_bucket: int) -> Mission:
    if duration_bucket not in STEPS_FOR:
        raise ValueError(f"duration_bucket must be one of {sorted(STEPS_FOR)}, got {duration_bucket}")

    if band not in template.bands:
        raise ValueError(f"template '{template.template_id}' has no '{band.value}' band")

    step_count = STEPS_FOR[duration_bucket]
    band_steps = sorted(template.bands[band].steps, key=lambda s: s.sequence)

    if len(band_steps) < step_count:
        raise ValueError(
            f"template '{template.template_id}' band '{band.value}' has only "
            f"{len(band_steps)} steps, needs {step_count} for a {duration_bucket}-minute mission"
        )

    truncated = band_steps[:step_count]
    title = template.bands[band].title or template.title

    return Mission(
        mission_id=str(uuid.uuid4()),
        template_id=template.template_id,
        title=title,
        age_band=band,
        estimated_minutes=duration_bucket,
        equipment=list(template.equipment),
        steps=[
            Step(
                sequence=step.sequence,
                prompt_text=step.prompt_text,
                verify_mode=step.verify_mode,
                prompt_id=step.prompt_id,
            )
            for step in truncated
        ],
    )
