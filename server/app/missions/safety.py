"""
validate_mission (B22) — the safety validator described in
content/schema/safety_constraints.yaml: one rejection rule per constraint,
checked here rather than by the generation prompt, never relaxed by a
template. The phrase lists are a coarse first pass — every template also
gets human review.

A rejected mission is never shown to a user; a different template is
served instead (B23/B30 handle that, this function only reports).
"""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel

from app.missions.models import MissionTemplate, ValidationResult
from app.models import Mission

CONSTRAINTS_PATH = Path(__file__).resolve().parents[2] / "content" / "schema" / "safety_constraints.yaml"


class SafetyConstraint(BaseModel):
    id: str
    rule: str
    rejects: list[str]


def load_constraints(path: Path = CONSTRAINTS_PATH) -> tuple[SafetyConstraint, ...]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    entries = raw.get("constraints", [])
    if not entries:
        raise ValueError(f"No safety constraints defined in {path}")
    return tuple(SafetyConstraint.model_validate(entry) for entry in entries)


CONSTRAINTS: tuple[SafetyConstraint, ...] = load_constraints()


def validate_mission(
    mission: Mission,
    template: MissionTemplate,
    constraints: tuple[SafetyConstraint, ...] = CONSTRAINTS,
) -> ValidationResult:
    failures: list[str] = []

    if mission.template_id != template.template_id:
        failures.append(
            f"mission.template_id '{mission.template_id}' does not match "
            f"template '{template.template_id}'"
        )

    for step in mission.steps:
        text = step.prompt_text.lower()
        for constraint in constraints:
            for phrase in constraint.rejects:
                if phrase.lower() in text:
                    failures.append(
                        f"step {step.sequence}: '{phrase}' violates {constraint.id} — {constraint.rule}"
                    )

    return ValidationResult(ok=not failures, failures=failures, warnings=[])
