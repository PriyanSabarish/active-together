"""
Loads content/taxonomy/mission_context_bindings.yaml's eligible_place_categories
per template — the real category-matching data for the reviewed library, since
every reviewed family uses category: "any" on the template itself (see
content/missions/CONTEXT.md: "the bindings use the dataset's seven actual
category codes, not the older placeholder mission categories").

Only eligible_place_categories is extracted here. The bindings file's other
fields — preference_codes (explicitly "unbound": no real frontend vocabulary
exists yet, per the file's own header) and parent_briefing (A35's concern,
delivering the safety briefing alongside a mission) — belong to other tasks
and aren't select_templates' job.

A template with no entry here, or an empty list, is treated as unbound —
matches every place, the same as it would with no bindings loaded at all —
rather than silently excluding content nobody has categorised yet.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from app.missions.loader import REPO_ROOT

DEFAULT_BINDINGS_PATH = REPO_ROOT / "content" / "taxonomy" / "mission_context_bindings.yaml"


def load_eligible_categories(path: Path = DEFAULT_BINDINGS_PATH) -> dict[str, list[str]]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return {
        entry["template_id"]: entry.get("eligible_place_categories", [])
        for entry in raw.get("templates", [])
    }
