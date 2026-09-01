"""
Base combo template library (task B7, supports B5).

Story 3.1 makes the existence of a base combo an eligibility condition.
Story 3.2 requires the card show the mapped activity type and the
corresponding category-level activity combo.

combos.json is organised by activity category, then by duration bucket:

    activity_type   what the child does there — "walking and exploring".
                    Distinct from the place's activity_category, which is what
                    the place is. One per category; the activity does not
                    change with duration, only its length does.

    template_id     stable internal identifier, for logging and for iteration
                    2's mission generation to key against.

    title           what the parent reads on the card.

OWNERSHIP: titles and activity types here are placeholders so that the payload
shape can be built and tested. Authoring the actual on-site activity content
is unassigned (backend tasks doc, section 5) and must be assigned before story
3.2 is satisfied. Replacing the text does not change any code in this module.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from app.models import DURATION_BUCKETS, ActivityCategory

COMBOS_PATH = Path(__file__).parent / "combos.json"


@dataclass(frozen=True)
class ComboTemplate:
    template_id: str      # internal identifier
    title: str            # shown to the parent
    activity_type: str    # what the child does there


def load_combos(path: Path = COMBOS_PATH) -> dict[tuple[str, int], ComboTemplate]:
    """Return a {(category, bucket): ComboTemplate} lookup.

    Every category must have a template in every bucket, so a missing one
    fails at import rather than silently making candidates ineligible during
    a search.
    """
    raw = json.loads(path.read_text(encoding="utf-8"))

    lookup: dict[tuple[str, int], ComboTemplate] = {}
    for category in ActivityCategory:
        entry = raw.get(category.value)
        if entry is None:
            raise ValueError(f"No combos defined for category '{category.value}'.")

        buckets_map = entry.get("buckets", {})
        for bucket in DURATION_BUCKETS:
            template = buckets_map.get(str(bucket))
            if template is None:
                raise ValueError(
                    f"No base combo for {category.value} at {bucket} minutes. "
                    f"Every category needs one in each of "
                    f"{len(DURATION_BUCKETS)} buckets."
                )
            lookup[(category.value, bucket)] = ComboTemplate(
                template_id=template["template_id"],
                title=template["title"],
                activity_type=entry["activity_type"],
            )

    return lookup


COMBOS: dict[tuple[str, int], ComboTemplate] = load_combos()


def find_combo(category: ActivityCategory | str, bucket: int) -> ComboTemplate | None:
    """Return the template for this category and bucket, or None."""
    key = category.value if isinstance(category, ActivityCategory) else category
    return COMBOS.get((key, bucket))