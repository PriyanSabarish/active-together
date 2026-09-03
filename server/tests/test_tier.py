from __future__ import annotations

import pytest

from app.models import Context, Tier
from app.recommendation.thresholds import THRESHOLDS
from app.recommendation.tier import assess
from tests import fixtures


def test_clear_weather_defaults_to_normal_tier():
    tier, summary = assess(fixtures.CLEAR_MILD)
    assert tier is Tier.NORMAL
    assert summary.warnings == ()
    assert summary.reminders == ()


@pytest.mark.parametrize(
    ("context", "expected_warning_count"),
    [
        (fixtures.RAIN_AT_THRESHOLD, 1),
        (fixtures.RAIN_HEAVY, 1),
        (fixtures.WIND_AT_THRESHOLD, 1),
        (fixtures.WIND_STRONG, 1),
        (fixtures.POOR_AIR_PM25, 1),
        (fixtures.POOR_AIR_PM10, 1),
        (fixtures.STORMY, 2),
        (fixtures.POOR_AIR_SEVERE, 2),
    ],
)
def test_exceeded_thresholds_deprioritise(context: Context, expected_warning_count: int):
    tier, summary = assess(context)
    assert tier is Tier.DEPRIORITISED
    assert len(summary.warnings) == expected_warning_count


def test_below_threshold_retains_normal_tier():
    tier, summary = assess(fixtures.RAIN_BELOW_THRESHOLD)
    assert tier is Tier.NORMAL
    assert summary.warnings == ()


def test_elevated_uv_adds_reminder_without_deprioritising():
    tier, summary = assess(fixtures.CLEAR_HIGH_UV)
    assert tier is Tier.NORMAL
    assert summary.warnings == ()
    assert len(summary.reminders) == 1


def test_low_uv_generates_no_reminders():
    _, summary = assess(fixtures.CLEAR_MILD)
    assert summary.reminders == ()


def test_simultaneous_warning_and_reminder():
    tier, summary = assess(fixtures.POOR_AIR_PM25)
    assert tier is Tier.DEPRIORITISED
    assert len(summary.warnings) == 1
    assert len(summary.reminders) == 1


def test_unavailable_forecast_remains_normal_tier():
    tier, summary = assess(fixtures.UNAVAILABLE)
    assert tier is Tier.NORMAL
    assert summary.available is False
    assert summary.warnings == ()
    assert summary.reminders == ()


def test_unavailable_readings_remain_none():
    _, summary = assess(fixtures.UNAVAILABLE)
    assert summary.precip_prob is None
    assert summary.temp_c is None


def test_partial_forecast_processes_available_fields_only():
    tier, summary = assess(fixtures.PARTIAL)
    assert tier is Tier.NORMAL
    assert summary.precip_prob == 0.30
    assert summary.wind_gust_kmh is None
    assert summary.warnings == ()


def test_unavailable_flag_ignores_residual_readings():
    stale_context = Context(available=False, precip_prob=0.95, wind_gust_kmh=70.0)
    tier, summary = assess(stale_context)
    assert tier is Tier.NORMAL
    assert summary.warnings == ()


def test_summary_preserves_context_readings():
    context = fixtures.CLEAR_MILD
    _, summary = assess(context)
    for field_name in ("temp_c", "precip_prob", "wind_gust_kmh", "uv_index", "pm25", "pm10"):
        assert getattr(summary, field_name) == getattr(context, field_name)


def test_emitted_messages_match_configured_thresholds():
    configured_messages = {t.message for t in THRESHOLDS}
    _, summary = assess(fixtures.POOR_AIR_SEVERE)
    assert set(summary.warnings) | set(summary.reminders) <= configured_messages


def test_warning_ordering_is_deterministic():
    first_warnings = assess(fixtures.STORMY)[1].warnings
    second_warnings = assess(fixtures.STORMY)[1].warnings
    assert first_warnings == second_warnings