"""Small standard-library Open-Meteo client with injectable transport."""

from __future__ import annotations

import json
from collections.abc import Callable, Sequence
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .models import Location


FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
AIR_QUALITY_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"
WEATHER_FIELDS = (
    "temperature_2m", "apparent_temperature", "precipitation_probability",
    "weather_code", "wind_speed_10m", "wind_gusts_10m",
)
AIR_FIELDS = ("uv_index", "pm2_5", "pm10")


class OpenMeteoError(RuntimeError):
    """The provider could not return a usable response."""


Transport = Callable[[str, float], Any]


def _default_transport(url: str, timeout: float) -> Any:
    request = Request(url, headers={"User-Agent": "active-together/1.0"})
    try:
        with urlopen(request, timeout=timeout) as response:
            return json.load(response)
    except Exception as exc:  # urllib exposes several transport-specific exceptions
        raise OpenMeteoError(str(exc)) from exc


class OpenMeteoClient:
    def __init__(self, timeout_seconds: float = 5.0, transport: Transport | None = None):
        self.timeout_seconds = timeout_seconds
        self.transport = transport or _default_transport

    @staticmethod
    def _url(base: str, fields: Sequence[str], locations: Sequence[Location]) -> str:
        if not locations:
            raise ValueError("At least one location is required")
        params = {
            "latitude": ",".join(str(item.latitude) for item in locations),
            "longitude": ",".join(str(item.longitude) for item in locations),
            "hourly": ",".join(fields),
            "timezone": "UTC",
            "forecast_days": "7",
        }
        return f"{base}?{urlencode(params)}"

    def fetch_weather(self, locations: Sequence[Location]) -> list[dict[str, Any]]:
        payload = self.transport(
            self._url(FORECAST_URL, WEATHER_FIELDS, locations), self.timeout_seconds
        )
        return self._attach_locations(payload, locations)

    def fetch_air_quality(self, locations: Sequence[Location]) -> list[dict[str, Any]]:
        payload = self.transport(
            self._url(AIR_QUALITY_URL, AIR_FIELDS, locations), self.timeout_seconds
        )
        return self._attach_locations(payload, locations)

    @staticmethod
    def _attach_locations(
        payload: Any, locations: Sequence[Location]
    ) -> list[dict[str, Any]]:
        records = payload if isinstance(payload, list) else [payload]
        if len(records) != len(locations) or not all(isinstance(x, dict) for x in records):
            raise OpenMeteoError("Unexpected number or shape of location responses")
        result = []
        for record, location in zip(records, locations, strict=True):
            item = dict(record)
            item["_location"] = location
            result.append(item)
        return result
