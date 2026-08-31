"""Shared product-facing models for live and cached environment data."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, Literal


DataMode = Literal["live", "cached"]
EnvironmentTier = Literal["normal", "deprioritised"]

#它表示一个天气查询地点，也就是三个 LGA 的代表点之一。
#frozen=True 表示创建后不能随意修改，避免请求过程中坐标被意外改变。
@dataclass(frozen=True, slots=True)
class Location:
    lga_code: str
    site_name: str
    display_name: str
    latitude: float
    longitude: float
#这是在线和离线模式共用的标准化数据：
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

#这是环境规则判断结果：
@dataclass(frozen=True, slots=True)
class EnvironmentAssessment:
    tier: EnvironmentTier
    show_uv_reminder: bool
    warnings: tuple[str, ...]
    unavailable_fields: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

#最终给后端的对象：
@dataclass(frozen=True, slots=True)
class EnvironmentResult:
    context: EnvironmentContext
    assessment: EnvironmentAssessment

    def to_dict(self) -> dict[str, Any]:
        return {
            "context": self.context.to_dict(),
            "assessment": self.assessment.to_dict(),
        }
