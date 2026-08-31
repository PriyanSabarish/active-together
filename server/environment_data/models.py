"""Shared product-facing models for live and cached environment data."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, Literal


DataMode = Literal["live", "cached"]
EnvironmentTier = Literal["normal", "deprioritised"]


@dataclass(frozen=True, slots=True)
class Location:
    lga_code: str
    site_name: str
    display_name: str
    latitude: float
    longitude: float


@dataclass(frozen=True, slots=True)
class EnvironmentContext:
    lga_code: str
    site_name: str
    display_name: str
    latitude: float
    longitude: float
    timestamp_utc: datetime
    timestamp_local: datetime
    fetched_at_utc: datetime
    source_mode: DataMode
    temperature_c: float | None = None
    apparent_temperature_c: float | None = None
    precipitation_probability_pct: float | None = None
    weather_code: int | None = None
    weather_description: str | None = None
    wind_speed_kmh: float | None = None
    wind_gusts_kmh: float | None = None
    uv_index: float | None = None
    pm2_5_ugm3: float | None = None
    pm10_ugm3: float | None = None
    weather_available: bool = True
    air_quality_available: bool = False

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        for key in ("timestamp_utc", "timestamp_local", "fetched_at_utc"):
            result[key] = result[key].isoformat()
        return result

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "EnvironmentContext":
        parsed = dict(value)
        for key in ("timestamp_utc", "timestamp_local", "fetched_at_utc"):
            parsed[key] = datetime.fromisoformat(parsed[key])
        return cls(**parsed)


@dataclass(frozen=True, slots=True)
class EnvironmentAssessment:
    tier: EnvironmentTier
    show_uv_reminder: bool
    warnings: tuple[str, ...]
    unavailable_fields: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class EnvironmentResult:
    context: EnvironmentContext
    assessment: EnvironmentAssessment

    def to_dict(self) -> dict[str, Any]:
        return {
            "context": self.context.to_dict(),
            "assessment": self.assessment.to_dict(),
        }
