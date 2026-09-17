"""
validate_schema (B21) — structural rules a mission template family must
satisfy beyond what Pydantic (B18) already enforces: every band matches
the family's step count, all bands agree with each other, and the
youngest band's wording stays short enough to hear once and act on.

Rules from content/schema/mission_template.schema.yaml covered here:
  - every band has exactly STEPS_FOR[duration_bucket] steps
  - all bands have the same step count
  - 5-7 wording is under 12 words per step

Deliberately not covered — each needs more than one template's worth of
data, or data this validator doesn't have access to, so they stay manual
review or a later task rather than a false sense of automated coverage:
  - prompt_id appears in prompts/vocabulary.yaml with status "kept"
    (waits on the B25 measurement — nothing is "kept" yet)
  - no two families share a step shape (needs the whole library, not one
    template)
  - bands differ in more than wording (not mechanically checkable)
  - no step names a site feature the source data cannot verify (needs
    the place/site dataset, not the template)
"""

from __future__ import annotations

from app.missions.builder import STEPS_FOR
from app.missions.models import MissionTemplate, ValidationResult
from app.models import AgeBand

MAX_WORDS_FOR_YOUNGEST_BAND = 12


def validate_schema(template: MissionTemplate) -> ValidationResult:
    failures: list[str] = []

    expected_count = STEPS_FOR[template.duration_bucket]
    step_counts = {band: len(band_data.steps) for band, band_data in template.bands.items()}

    for band, count in step_counts.items():
        if count != expected_count:
            failures.append(
                f"band '{band.value}' has {count} steps, expected {expected_count} "
                f"for a {template.duration_bucket}-minute family"
            )

    if len(set(step_counts.values())) > 1:
        failures.append(
            "bands do not all have the same step count: "
            + ", ".join(f"{band.value}={count}" for band, count in step_counts.items())
        )

    band_5_7 = template.bands.get(AgeBand.BAND_5_7)
    if band_5_7 is not None:
        for step in band_5_7.steps:
            word_count = len(step.prompt_text.split())
            if word_count > MAX_WORDS_FOR_YOUNGEST_BAND:
                failures.append(
                    f"5-7 band step {step.sequence} has {word_count} words "
                    f"(max {MAX_WORDS_FOR_YOUNGEST_BAND}): '{step.prompt_text}'"
                )

    return ValidationResult(ok=not failures, failures=failures, warnings=[])
