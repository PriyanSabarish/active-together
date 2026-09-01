""""
Shared types for backend A and backend B
Backend A produces Place and Context; Backend B consumes them and produces Recommendation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional

# Domain bounds & API constraints
ALLOWED_RADIUS_KM = (3, 5, 10)
DURATION_MIN_BOUNDS = (20, 120)
DURATION_BUCKETS = (20, 40, 60)



# Enum - fixed variables 

class RecommendationRequest(BaseModel):
    latitude: float = Field(..., description="User latitude")
    longitude: float = Field(..., description="User longitude")
    radius_km: Optional[float] = Field(5.0, description="Search radius in kilometers")
    duration_min: Optional[int] = Field(60, description="Activity duration in minutes")

class ActivityCategory(str, Enum):
    """seven categoris produced by Vicmap"""
    PLAYGROUND = "playground"
    PARK_AND_GARDEN = "park_and_garden"
    SPORTS_GROUND = "sports_ground"
    COURT = "court"
    TRAIL_ACCESS = "trail_access"
    SKATE_BMX = "skate_bmx"
    PICNIC_DAY_USE = "picnic_day_use"


class Tier(str, Enum):
    """environmental tier, normal-tier combos are always ordered first"""
    NORMAL = "normal"
    DEPRIORITISED = "deprioritised"


class RecommendationStatus(str, Enum):
    OK = "ok"
    ZERO_RESULTS = "zero_results"


# Backend A: Data & Ingestion Models 


@dataclass(frozen=True)
class Place:
    place_id: str
    display_name: str | None
    activity_category: ActivityCategory
    lga_name: str
    latitude: float
    longitude: float
    distance_m: int
    classification_confidence: float


@dataclass(frozen=True)
class Context:
    available: bool
    temp_c: float | None = None
    precip_prob: float | None = None
    wind_gust_kmh: float | None = None
    uv_index: float | None = None
    pm25: float | None = None
    pm10: float | None = None


# Backend B: Recommendation Models 


@dataclass(frozen=True)
class EnvironmentalSummary:
    """
        what the client renders on a combo card. Mirrors Context but carries the
        warnings that were derived from it, so the client does not re-implement
        threshold logic.
    """
    available: bool
    temp_c: float | None = None
    precip_prob: float | None = None
    wind_gust_kmh: float | None = None
    uv_index: float | None = None
    pm25: float | None = None
    pm10: float | None = None
    warnings: tuple[str, ...] = ()
    reminders: tuple[str, ...] = ()


@dataclass(frozen=True)
class Combo:
    place: Place
    activity_type: str
    entered_duration_min: int
    duration_bucket: int
    combo_template: str
    tier: Tier
    environmental_summary: EnvironmentalSummary
    explanation: str


@dataclass(frozen=True)
class Recommendation:
    status: RecommendationStatus
    combos: tuple[Combo, ...] = ()
    message: str | None = None


# Client Requests


@dataclass(frozen=True)
class SearchRequest:
    latitude: float
    longitude: float
    radius_km: int
    timestamp: str
    duration_min: int