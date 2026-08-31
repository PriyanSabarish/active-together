"""Convert provider payloads into the shared EnvironmentContext schema."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from zoneinfo import ZoneInfo

from .models import EnvironmentContext, Location
from .weather_codes import WMO_WEATHER_LABELS


LOCAL_TZ = ZoneInfo("Australia/Sydney")
WEATHER_MAP = {
    "temperature_2m": "temperature_c",
    "apparent_temperature": "apparent_temperature_c",
    "precipitation_probability": "precipitation_probability_pct",
    "weather_code": "weather_code",
    "wind_speed_10m": "wind_speed_kmh",
    "wind_gusts_10m": "wind_gusts_kmh",
}
AIR_MAP = {"uv_index": "uv_index", "pm2_5": "pm2_5_ugm3", "pm10": "pm10_ugm3"}


class NormalizationError(ValueError):
    pass


def _hourly_rows(payload: dict[str, Any], required: tuple[str, ...]) -> dict[datetime, dict[str, Any]]:
    hourly = payload.get("hourly")
    if not isinstance(hourly, dict) or not isinstance(hourly.get("time"), list):
        raise NormalizationError("Response has no hourly time array")
    missing = [key for key in required if key not in hourly]
    if missing:
        raise NormalizationError(f"Missing hourly fields: {missing}")
    count = len(hourly["time"])
    if any(not isinstance(hourly[key], list) or len(hourly[key]) != count for key in required):
        raise NormalizationError("Hourly arrays do not have equal lengths")
    rows: dict[datetime, dict[str, Any]] = {}
    for index, raw_time in enumerate(hourly["time"]):
        timestamp = datetime.fromisoformat(raw_time).replace(tzinfo=UTC)
        if timestamp in rows:
            raise NormalizationError(f"Duplicate timestamp: {timestamp.isoformat()}")
        rows[timestamp] = {key: hourly[key][index] for key in required}
    return rows


def normalize_location(
    weather_payload: dict[str, Any],
    air_payload: dict[str, Any] | None,
    fetched_at_utc: datetime,
    source_mode: str,
) -> list[EnvironmentContext]:
    location = weather_payload.get("_location")
    if not isinstance(location, Location):
        raise NormalizationError("Weather response is missing location metadata")
    weather = _hourly_rows(weather_payload, tuple(WEATHER_MAP))
    air: dict[datetime, dict[str, Any]] = {}
    if air_payload is not None:
        air = _hourly_rows(air_payload, tuple(AIR_MAP))

    contexts = []
    for timestamp, weather_values in weather.items():
        air_values = air.get(timestamp)
        weather_code = weather_values["weather_code"]
        if weather_code is not None:
            weather_code = int(weather_code)
            if weather_code not in WMO_WEATHER_LABELS:
                raise NormalizationError(f"Unknown WMO weather code: {weather_code}")
        values = {target: weather_values[source] for source, target in WEATHER_MAP.items()}
        values["weather_code"] = weather_code
        values["weather_description"] = WMO_WEATHER_LABELS.get(weather_code)
        if air_values is not None:
            values.update({target: air_values[source] for source, target in AIR_MAP.items()})
        contexts.append(EnvironmentContext(
            lga_code=location.lga_code,
            site_name=location.site_name,
            display_name=location.display_name,
            latitude=location.latitude,
            longitude=location.longitude,
            timestamp_utc=timestamp,
            timestamp_local=timestamp.astimezone(LOCAL_TZ),
            fetched_at_utc=fetched_at_utc,
            source_mode=source_mode,  # type: ignore[arg-type]
            weather_available=True,
            air_quality_available=air_values is not None and all(
                air_values.get(key) is not None for key in AIR_MAP
            ),
            **values,
        ))
    return contexts


def normalize_all(
    weather_payloads: list[dict[str, Any]],
    air_payloads: list[dict[str, Any]] | None,
    fetched_at_utc: datetime | None = None,
    source_mode: str = "live",
) -> list[EnvironmentContext]:
    fetched = fetched_at_utc or datetime.now(UTC)
    air_by_site = {
        item["_location"].site_name: item for item in (air_payloads or [])
    }
    result = []
    for weather in weather_payloads:
        site_name = weather["_location"].site_name
        result.extend(normalize_location(
            weather, air_by_site.get(site_name), fetched, source_mode
        ))
    return sorted(result, key=lambda item: (item.site_name, item.timestamp_utc))
