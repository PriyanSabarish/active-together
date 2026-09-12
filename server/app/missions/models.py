"""
Mission template schema (B18) — Pydantic models mirroring the frozen family
schema at content/schema/mission_template.schema.yaml.

These models enforce structure only: required fields, types, and the one
field-presence rule tied to a sibling field (prompt_id required when
verify_mode is photo). Cross-band and cross-template consistency rules —
step counts matching the duration bucket, the 12-word limit for the 5-7
band, prompt_id membership in the measured vocabulary, no two families
sharing a step shape — belong to the schema validator (B21) and safety
validator (B22), not here. Change a field on any of these only by pull
request, per the schema file's own rule, since Content authors against it
directly.

Mission and Step — the shapes that actually cross the wire to Backend A —
live in app.models, not here; this module only imports their enums.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, model_validator

from app.models import AgeBand, VerifyMode

DURATION_BUCKETS = (20, 40, 60)


class Mechanic(str, Enum):
    FIND = "find"
    MOVE = "move"
    COUNT = "count"
    IMAGINE = "imagine"
    SEQUENCE = "sequence"


class WeatherTag(str, Enum):
    ANY = "any"
    DRY = "dry"
    WET = "wet"
    WINDY = "windy"
    HOT = "hot"
    COLD = "cold"
    OVERCAST = "overcast"


class SiteRequirement(str, Enum):
    BARE_SITE = "bare_site"
    GRASS = "grass"
    TREES = "trees"
    PATH = "path"
    OPEN_SPACE = "open_space"
    PLAY_EQUIPMENT = "play_equipment"
    WATER_ADJACENT = "water_adjacent"
    SEATING = "seating"


class SafetyTag(str, Enum):
    INHERITED = "inherited"


class ReviewStatus(str, Enum):
    DRAFT = "draft"
    REVIEWED = "reviewed"


class TemplateStep(BaseModel):
    sequence: int
    prompt_text: str
    verify_mode: VerifyMode
    prompt_id: Optional[str] = None
    variable: bool

    @model_validator(mode="after")
    def _prompt_id_required_for_photo(self) -> "TemplateStep":
        if self.verify_mode is VerifyMode.PHOTO and not self.prompt_id:
            raise ValueError("prompt_id is required when verify_mode is 'photo'")
        return self


class Band(BaseModel):
    title: Optional[str] = None
    steps: list[TemplateStep]


class Review(BaseModel):
    author: str
    reviewed_by: Optional[str] = None
    status: ReviewStatus


class MissionTemplate(BaseModel):
    """One template family: up to nine cells, three age bands by three
    duration buckets. duration_bucket is the longest bucket this family
    covers; a shorter mission is a prefix of a band's step list."""

    template_id: str
    title: str
    category: str  # an ActivityCategory code, or "any" for bare-site families
    duration_bucket: int
    weather_tags: list[WeatherTag]
    site_requirements: list[SiteRequirement]
    equipment: list[str] = Field(default_factory=list)
    mechanic: Mechanic
    bands: dict[AgeBand, Band]
    safety_tags: list[SafetyTag]
    review: Review

    @model_validator(mode="after")
    def _duration_bucket_is_valid(self) -> "MissionTemplate":
        if self.duration_bucket not in DURATION_BUCKETS:
            raise ValueError(f"duration_bucket must be one of {DURATION_BUCKETS}")
        return self

    @model_validator(mode="after")
    def _at_least_one_band(self) -> "MissionTemplate":
        if not self.bands:
            raise ValueError("a template family must define at least one band")
        return self
