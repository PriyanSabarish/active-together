from __future__ import annotations

import tempfile
import unittest
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path

from server.environment_data.cache import CacheRepository, ForecastNotCached
from server.environment_data.locations import load_locations
from server.environment_data.models import EnvironmentContext
from server.environment_data.normalizer import normalize_all
from server.environment_data.open_meteo_client import OpenMeteoClient, OpenMeteoError
from server.environment_data.policy import assess_environment
from server.environment_data.service import EnvironmentService


NOW = datetime(2026, 8, 31, 0, tzinfo=UTC)


def payload(location, *, rain=10, gust=20, uv=2, pm25=5, pm10=10, air=False):
    hourly = {
        "time": ["2026-08-31T00:00", "2026-08-31T01:00"],
    }
    if air:
        hourly.update({"uv_index": [uv, uv], "pm2_5": [pm25, pm25], "pm10": [pm10, pm10]})
    else:
        hourly.update({
            "temperature_2m": [15, 16],
            "apparent_temperature": [14, 15],
            "precipitation_probability": [rain, rain],
            "weather_code": [1, 2],
            "wind_speed_10m": [10, 11],
            "wind_gusts_10m": [gust, gust],
        })
    return {"hourly": hourly, "_location": location}


def context(site_name="melbourne", **changes):
    location = load_locations()[site_name]
    base = EnvironmentContext(
        lga_code=location.lga_code,
        site_name=location.site_name,
        display_name=location.display_name,
        latitude=location.latitude,
        longitude=location.longitude,
        timestamp_utc=NOW,
        timestamp_local=NOW,
        fetched_at_utc=NOW,
        source_mode="live",
        temperature_c=15,
        apparent_temperature_c=14,
        precipitation_probability_pct=10,
        weather_code=1,
        weather_description="mainly_clear",
        wind_speed_kmh=10,
        wind_gusts_kmh=20,
        uv_index=2,
        pm2_5_ugm3=5,
        pm10_ugm3=10,
        weather_available=True,
        air_quality_available=True,
    )
    return replace(base, **changes)


def seven_day_contexts():
    return [
        replace(context(site), timestamp_utc=NOW + timedelta(hours=hour))
        for site in ("melton", "melbourne", "monash")
        for hour in range(168)
    ]


class LocationTests(unittest.TestCase):
    def test_exactly_three_pilot_locations(self):
        locations = load_locations()
        self.assertEqual(set(locations), {"melton", "melbourne", "monash"})
        self.assertEqual(locations["melbourne"].lga_code, "24600")


class PolicyTests(unittest.TestCase):
    def test_threshold_boundaries_deprioritise(self):
        item = context(
            precipitation_probability_pct=60,
            wind_gusts_kmh=40,
            pm2_5_ugm3=25,
            pm10_ugm3=80,
            uv_index=3,
        )
        result = assess_environment(item)
        self.assertEqual(result.tier, "deprioritised")
        self.assertTrue(result.show_uv_reminder)
        self.assertEqual(len(result.warnings), 4)

    def test_uv_alone_does_not_deprioritise(self):
        result = assess_environment(context(uv_index=8))
        self.assertEqual(result.tier, "normal")
        self.assertTrue(result.show_uv_reminder)

    def test_missing_air_is_explicit_not_invented(self):
        result = assess_environment(context(
            air_quality_available=False, uv_index=None, pm2_5_ugm3=None, pm10_ugm3=None
        ))
        self.assertEqual(result.tier, "normal")
        self.assertIn("air_quality", result.unavailable_fields)


class NormalizerTests(unittest.TestCase):
    def test_weather_survives_missing_air_response(self):
        location = load_locations()["monash"]
        records = normalize_all([payload(location)], None, NOW, "live")
        self.assertEqual(len(records), 2)
        self.assertTrue(records[0].weather_available)
        self.assertFalse(records[0].air_quality_available)
        self.assertIsNone(records[0].pm2_5_ugm3)

    def test_weather_and_air_join_by_utc_hour(self):
        location = load_locations()["melton"]
        records = normalize_all(
            [payload(location)], [payload(location, air=True, uv=4)], NOW, "live"
        )
        self.assertTrue(records[0].air_quality_available)
        self.assertEqual(records[0].uv_index, 4)
        self.assertEqual(records[0].timestamp_utc.tzinfo, UTC)


class CacheTests(unittest.TestCase):
    def test_round_trip_and_hour_floor(self):
        with tempfile.TemporaryDirectory() as directory:
            repository = CacheRepository(Path(directory))
            repository.write_offline_bundle(seven_day_contexts())
            found = repository.find(
                "monash", datetime(2026, 8, 31, 0, 45, tzinfo=UTC)
            )
            self.assertEqual(found.source_mode, "cached")
            self.assertEqual(found.site_name, "monash")

    def test_out_of_range_is_not_extrapolated(self):
        with tempfile.TemporaryDirectory() as directory:
            repository = CacheRepository(Path(directory))
            repository.write_offline_bundle(seven_day_contexts())
            with self.assertRaises(ForecastNotCached):
                repository.find("melton", datetime(2026, 9, 8, tzinfo=UTC))


class ServiceTests(unittest.TestCase):
    def test_live_failure_uses_offline_bundle(self):
        def failing_transport(url, timeout):
            raise OpenMeteoError("offline")

        with tempfile.TemporaryDirectory() as directory:
            repository = CacheRepository(Path(directory))
            repository.write_offline_bundle(seven_day_contexts())
            service = EnvironmentService(
                OpenMeteoClient(transport=failing_transport), repository
            )
            result = service.get_context("melbourne", NOW)
            self.assertEqual(result.context.source_mode, "cached")

    def test_live_air_failure_returns_weather_and_persists_it(self):
        location = load_locations()["melbourne"]

        def partial_transport(url, timeout):
            if "air-quality" in url:
                raise OpenMeteoError("air unavailable")
            item = payload(location)
            item.pop("_location")
            return item

        with tempfile.TemporaryDirectory() as directory:
            repository = CacheRepository(Path(directory))
            service = EnvironmentService(
                OpenMeteoClient(transport=partial_transport), repository
            )
            result = service.get_context("melbourne", NOW)
            self.assertEqual(result.context.source_mode, "live")
            self.assertFalse(result.context.air_quality_available)
            self.assertTrue(repository.live_path.exists())


if __name__ == "__main__":
    unittest.main()
