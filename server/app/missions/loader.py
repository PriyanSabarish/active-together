"""Loads content/missions/*.yaml into MissionTemplate objects.

Structural validation only (Pydantic, via MissionTemplate) — this is what
turns "the schema is frozen" into "authoring is unblocked," since a content
author can run this against a draft file before opening a pull request.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from app.missions.models import MissionTemplate


def load_template_file(path: Path) -> list[MissionTemplate]:
    """Parse one content/missions/*.yaml file into its template families."""
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    templates = raw.get("templates", [])
    return [MissionTemplate.model_validate(entry) for entry in templates]


def load_template_dir(directory: Path) -> list[MissionTemplate]:
    """Parse every *.yaml file directly under directory (non-recursive, so a
    _candidates/ subfolder of drafts is skipped)."""
    families: list[MissionTemplate] = []
    for path in sorted(directory.glob("*.yaml")):
        families.extend(load_template_file(path))
    return families
