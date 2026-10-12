"""Parent guides for the at-home activities (story 9.2).

The mission steps the app receives are short; the setup, safety rules, clue
answers and what to say for each stage live in
content/missions/home_parent_guides.json. This is the one copy of that text:
the server sends the matching guide with each home mission, and the client only
displays it. Step N of a mission is stage N of its guide.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel, Field

GUIDES_PATH = Path(__file__).resolve().parents[2] / "content" / "missions" / "home_parent_guides.json"
AGE_BANDS = ("5-7", "8-10", "11-12")


class GuidePart(BaseModel):
    label: str | None = None
    read: str | None = None
    do: list[str] = Field(default_factory=list)
    bands: dict[str, str] = Field(default_factory=dict)
    hint: str | None = None


class GuideStage(BaseModel):
    title: str
    parts: list[GuidePart] = Field(min_length=1)
    closing: str | None = None


class ParentGuide(BaseModel):
    setupTime: str
    kit: list[str] = Field(min_length=1)
    setup: list[str] = Field(min_length=1)
    opening: str
    stages: list[GuideStage] = Field(min_length=3)


@lru_cache(maxsize=1)
def _load() -> tuple[tuple[str, ...], dict[str, ParentGuide]]:
    raw = json.loads(GUIDES_PATH.read_text(encoding="utf-8"))
    rules = tuple(raw["rules"])
    guides = {template_id: ParentGuide(**g) for template_id, g in raw["guides"].items()}
    for template_id, guide in guides.items():
        for stage in guide.stages:
            for part in stage.parts:
                unknown = set(part.bands) - set(AGE_BANDS)
                if unknown:
                    raise ValueError(f"{template_id}: unknown age band(s) {sorted(unknown)}")
    return rules, guides


def guide_for(template_id: str) -> dict | None:
    """The guide for one template, with the shared safety rules, as plain JSON
    data. None when the template has no guide (every outdoor template)."""
    rules, guides = _load()
    guide = guides.get(template_id)
    if guide is None:
        return None
    return {"rules": list(rules), **guide.model_dump(mode="json", exclude_none=True)}


def guided_template_ids() -> frozenset[str]:
    return frozenset(_load()[1])
