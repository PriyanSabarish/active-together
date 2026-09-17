"""Loads mission template family YAML into MissionTemplate objects.

Structural validation only (Pydantic, via MissionTemplate) — this is what
turns "the schema is frozen" into "authoring is unblocked," since a content
author can run this against a draft file before opening a pull request.

DEFAULT_MISSIONS_DIR points at content/missions/reviewed/ — the 18 families
authored by Jiabin and reviewed by lychen (see content/missions/MIGRATION.md)
are the real, review-approved library. content/missions/*.yaml at the top
level are older, superseded placeholder category files (MIGRATION.md: "the
older category mission files are outside this migration collection") — kept
as-is, not deleted, but not what generate_missions/select_templates should
load by default.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from app.missions.models import MissionTemplate

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_MISSIONS_DIR = REPO_ROOT / "content" / "missions" / "reviewed"


def load_template_file(path: Path) -> list[MissionTemplate]:
    """Parse one mission family YAML file into its template families."""
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    templates = raw.get("templates", [])
    return [MissionTemplate.model_validate(entry) for entry in templates]


def load_template_dir(directory: Path = DEFAULT_MISSIONS_DIR) -> list[MissionTemplate]:
    """Parse every *.yaml file directly under directory (non-recursive, so a
    _candidates/ subfolder of drafts is skipped)."""
    families: list[MissionTemplate] = []
    for path in sorted(directory.glob("*.yaml")):
        families.extend(load_template_file(path))
    return families
