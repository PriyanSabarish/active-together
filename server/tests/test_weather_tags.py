from __future__ import annotations

from app.missions.models import WeatherTag
from app.missions.weather_tags import classify_weather_tags
from app.models import Context


def _context(**overrides) -> Context:
    defaults = dict(available=True, temp_c=20.0, precip_prob=0.10, wind_gust_kmh=10.0)
    return Context(**{**defaults, **overrides})


def test_any_is_always_present():
    assert WeatherTag.ANY in classify_weather_tags(_context())


def test_dry_when_precip_below_threshold():
    tags = classify_weather_tags(_context(precip_prob=0.59))
    assert WeatherTag.DRY in tags
    assert WeatherTag.WET not in tags


def test_wet_at_threshold():
    tags = classify_weather_tags(_context(precip_prob=0.60))
    assert WeatherTag.WET in tags
    assert WeatherTag.DRY not in tags


def test_dry_when_precip_missing():
    tags = classify_weather_tags(_context(precip_prob=None))
    assert WeatherTag.DRY in tags
    assert WeatherTag.WET not in tags


def test_windy_at_threshold():
    assert WeatherTag.WINDY in classify_weather_tags(_context(wind_gust_kmh=40.0))


def test_not_windy_below_threshold():
    assert WeatherTag.WINDY not in classify_weather_tags(_context(wind_gust_kmh=39.9))


def test_hot_at_threshold():
    assert WeatherTag.HOT in classify_weather_tags(_context(temp_c=30.0))


def test_cold_at_threshold():
    assert WeatherTag.COLD in classify_weather_tags(_context(temp_c=12.0))


def test_neither_hot_nor_cold_in_between():
    tags = classify_weather_tags(_context(temp_c=20.0))
    assert WeatherTag.HOT not in tags
    assert WeatherTag.COLD not in tags


def test_overcast_is_never_produced():
    tags = classify_weather_tags(_context(precip_prob=0.9, wind_gust_kmh=60.0, temp_c=35.0))
    assert WeatherTag.OVERCAST not in tags


def test_unavailable_context_still_classifies_dry_and_any():
    tags = classify_weather_tags(Context(available=False))
    assert tags == {WeatherTag.ANY, WeatherTag.DRY}
