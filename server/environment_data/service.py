"""Live-first environment service with transparent validated-cache fallback."""

from __future__ import annotations

from datetime import UTC, datetime

from .cache import CacheRepository, ForecastNotCached, floor_hour
from .locations import load_locations
from .models import EnvironmentResult
from .normalizer import NormalizationError, normalize_all
from .open_meteo_client import OpenMeteoClient, OpenMeteoError
from .policy import assess_environment


class EnvironmentUnavailable(RuntimeError):
    pass


class UnknownPilotLocation(ValueError):
    pass


class EnvironmentService:
    def __init__(self, client: OpenMeteoClient, repository: CacheRepository):
        self.client = client
        self.repository = repository
        self.locations = load_locations()

    def refresh_offline_bundle(self) -> int:
        """Download and atomically replace the three-LGA seven-day bundle."""
        locations = list(self.locations.values())
        fetched_at = datetime.now(UTC)
        weather = self.client.fetch_weather(locations)
        try:
            air = self.client.fetch_air_quality(locations)
        except OpenMeteoError:
            air = None
        contexts = self._normalize_with_optional_air(weather, air, fetched_at, "cached")
        self.repository.write_offline_bundle(contexts)
        return len(contexts)

    def get_context(self, site_name: str, requested_at: datetime) -> EnvironmentResult:
        location = self.locations.get(site_name)
        if location is None:
            raise UnknownPilotLocation(
                f"{site_name!r} is outside the pilot locations: {sorted(self.locations)}"
            )
        target = floor_hour(requested_at)
        try:
            fetched_at = datetime.now(UTC)
            weather = self.client.fetch_weather([location])
            try:
                air = self.client.fetch_air_quality([location])
            except OpenMeteoError:
                air = None
            contexts = self._normalize_with_optional_air(weather, air, fetched_at, "live")
            self.repository.write_live_forecast(contexts)
            context = next(item for item in contexts if item.timestamp_utc == target)
        except (OpenMeteoError, NormalizationError, StopIteration):
            try:
                context = self.repository.find(site_name, target)
            except ForecastNotCached as exc:
                raise EnvironmentUnavailable(str(exc)) from exc
        return EnvironmentResult(context=context, assessment=assess_environment(context))

    @staticmethod
    def _normalize_with_optional_air(weather, air, fetched_at, source_mode):
        # Validate weather independently so a malformed AQ response can safely degrade
        # to explicit AQ-unavailable values instead of discarding valid weather.
        weather_only = normalize_all(weather, None, fetched_at, source_mode)
        if air is None:
            return weather_only
        try:
            return normalize_all(weather, air, fetched_at, source_mode)
        except NormalizationError:
            return weather_only
