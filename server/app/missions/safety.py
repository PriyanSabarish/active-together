"""
validate_mission (B22, B59) — the safety validator described in
content/schema/safety_constraints.yaml: one rejection rule per constraint,
checked here rather than by the generation prompt, never relaxed by a
template. The phrase lists are a coarse first pass — every template also
gets human review.

Story 5.4 / Epic 9: setting = home applies two extra safety constraints
(no climbing on furniture, no throwing hard objects) alongside the existing
nine constraints.

A rejected mission is never shown to a user; a different template is
served instead (B23/B30 handle that, this function only reports).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel

from app.missions.models import MissionTemplate, ValidationResult
from app.models import Mission, Setting

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


def load_home_constraints(path: Path = CONSTRAINTS_PATH) -> tuple[SafetyConstraint, ...]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    entries = raw.get("home_constraints", [])
    if not entries:
        raise ValueError(f"No home safety constraints defined in {path}")
    return tuple(SafetyConstraint.model_validate(entry) for entry in entries)


CONSTRAINTS: tuple[SafetyConstraint, ...] = load_constraints()
HOME_CONSTRAINTS: tuple[SafetyConstraint, ...] = load_home_constraints()


def validate_mission(
    mission: Mission,
    template_or_setting: MissionTemplate | Setting | str | None = None,
    constraints: tuple[SafetyConstraint, ...] | None = None,
    *,
    setting: Setting | str | None = None,
) -> ValidationResult:
    template: Any = None
    resolved_setting: str = "outdoor"

    if isinstance(template_or_setting, (Setting, str)):
        resolved_setting = template_or_setting.value if isinstance(template_or_setting, Setting) else template_or_setting
    elif isinstance(template_or_setting, MissionTemplate):
        template = template_or_setting
    elif template_or_setting is not None:
        template = template_or_setting

    if setting is not None:
        resolved_setting = setting.value if isinstance(setting, Setting) else setting

    is_home = resolved_setting.lower() == "home"

    if constraints is not None:
        active_constraints = constraints
    elif is_home:
        active_constraints = CONSTRAINTS + HOME_CONSTRAINTS
    else:
        active_constraints = CONSTRAINTS

    failures: list[str] = []

    if template is not None:
        template_id = getattr(template, "template_id", None)
        if isinstance(template, dict):
            template_id = template.get("template_id", template_id)
        if template_id is not None and mission.template_id != template_id:
            failures.append(
                f"mission.template_id '{mission.template_id}' does not match "
                f"template '{template_id}'"
            )

    for step in mission.steps:
        text = step.prompt_text.lower()
        for constraint in active_constraints:
            for phrase in constraint.rejects:
                if phrase.lower() in text:
                    failures.append(
                        f"step {step.sequence}: '{phrase}' violates {constraint.id} — {constraint.rule}"
                    )

    return ValidationResult(ok=not failures, failures=failures, warnings=[])
