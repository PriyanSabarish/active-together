"""
Shared types for Backend A and Backend B. 
Updated to support settings (outdoor, home, indoor_place), 
travel modes, and indoor place schemas.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional, Literal

from app.models import AgeBand


class SettingEnum(str, Enum):
    OUTDOOR = "outdoor"
    HOME = "home"
    INDOOR_PLACE = "indoor_place"


class TravelModeEnum(str, Enum):
    WALKING = "walking"
    CYCLING = "cycling"
    DRIVING = "driving"


class ActivityCategory(str, Enum):
    """Seven core categories produced by Vicmap"""
    PLAYGROUND = "playground"
    PARK_AND_GARDEN = "park_and_garden"
    SPORTS_GROUND = "sports_ground"
    COURT = "court"
    TRAIL_ACCESS = "trail_access"
    SKATE_BMX = "skate_bmx"
    PICNIC_DAY_USE = "picnic_day_use"


class RecommendationRequest(BaseModel):
    setting: SettingEnum = Field(SettingEnum.OUTDOOR, description="Environment setting: outdoor, home, or indoor_place")
    latitude: Optional[float] = Field(None, description="User latitude; required for outdoor and indoor_place, ignored when setting = home")
    longitude: Optional[float] = Field(None, description="User longitude; required for outdoor and indoor_place, ignored when setting = home")
    radius_km: Optional[int] = Field(5, description="Search radius in kilometers (3 | 5 | 10)")
    timestamp: Optional[str] = Field(None, description="ISO timestamp within forecast range")
    duration_min: Optional[int] = Field(60, description="Total activity duration in minutes")
    travel_mode: TravelModeEnum = Field(TravelModeEnum.WALKING, description="Mode of travel")
    travel_limit_min: Optional[int] = Field(None, description="Longest one-way travel, 5 to 30 in steps of 5; enables spread ranking")
    ranking_mode: Optional[str] = Field(None, description="'spread' or 'nearest'; missing or unknown uses the server default")
    excluded_categories: list[str] = Field(default_factory=list)
    recent_template_ids: list[str] = Field(default_factory=list, description="Recently played templates to avoid repeating (home)")
    age_band: Optional[AgeBand] = Field(None, description="5-7 | 8-10 | 11-12; required when setting = home")


@dataclass(frozen=True)
class TravelTime:
    minutes: int
    source: Literal["openrouteservice", "estimate"]


@dataclass(frozen=True)
class Place:
    place_id: str | None
    display_name: str | None
    activity_category: str | None
    lga_name: str | None
    latitude: float | None
    longitude: float | None
    distance_m: int | None
    classification_confidence: float | None
    unverified: bool = False


@dataclass(frozen=True)
class Context:
    available: bool
    temp_c: float | None = None
    precip_prob: float | None = None
    wind_gust_kmh: float | None = None
    uv_index: float | None = None
    pm25: float | None = None
    pm10: float | None = None