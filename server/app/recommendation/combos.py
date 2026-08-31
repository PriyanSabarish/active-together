"""
Base combo template registry and lookup utilities.

Loads pre-configured combo templates for activity categories and duration
buckets from disk, ensuring complete coverage across all combinations.
"""

from __future__ import annotations

import json
from pathlib import Path

from app.models import DURATION_BUCKETS, ActivityCategory

COMBOS_PATH = Path(__file__).parent / "combos.json"


def load_combos(path: Path = COMBOS_PATH) -> dict[str, str]:
    raw = json.loads(path.read_text(encoding="utf-8"))

    lookup: dict[str, str] = {}
    for category in ActivityCategory:
        for bucket in DURATION_BUCKETS:
            key = f"{category.value}.{bucket}"
            if key not in raw:
                raise ValueError(
                    f"Missing combo template for '{key}'. "
                    f"All {len(ActivityCategory)} categories require entries for buckets {DURATION_BUCKETS}."
                )
            lookup[key] = raw[key]["template_id"]

    return lookup


COMBOS: dict[str, str] = load_combos()


def find_combo(category: ActivityCategory, bucket: int) -> str | None:
    return COMBOS.get(f"{category.value}.{bucket}")