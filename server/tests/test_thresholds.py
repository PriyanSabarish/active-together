from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.recommendation.thresholds import (
    DEPRIORITISE,
    REMIND,
    THRESHOLDS,
    load_thresholds,
)
from tests import fixtures

BY_FIELD = {t.field: t for t in THRESHOLDS}


def test_all_expected_fields_configured():
    assert set(BY_FIELD) == {"precip_prob", "wind_gust_kmh", "pm25", "pm10", "uv_index"}


@pytest.mark.parametrize(
    ("field_name", "expected_value", "expected_effect"),
    [
        ("precip_prob", 0.60, DEPRIORITISE),
        ("wind_gust_kmh", 40.0, DEPRIORITISE),
        ("pm25", 25.0, DEPRIORITISE),
        ("pm10", 80.0, DEPRIORITISE),
        ("uv_index", 3.0, REMIND),
    ],
)
def test_threshold_values_and_effects(
    field_name: str, expected_value: float, expected_effect: str
):
    threshold = BY_FIELD[field_name]
    assert threshold.value == expected_value
    assert threshold.effect == expected_effect


def test_threshold_comparison_is_inclusive():
    rain = BY_FIELD["precip_prob"]
    assert rain.triggers(0.60)
    assert not rain.triggers(0.59)


def test_missing_reading_never_triggers():
    assert not BY_FIELD["precip_prob"].triggers(None)


def test_threshold_metadata_present():
    for threshold in THRESHOLDS:
        assert threshold.source.strip()
        assert threshold.message.strip()


@pytest.mark.parametrize(
    ("context", "field_name"),
    [
        (fixtures.RAIN_AT_THRESHOLD, "precip_prob"),
        (fixtures.WIND_AT_THRESHOLD, "wind_gust_kmh"),
        (fixtures.POOR_AIR_PM25, "pm25"),
        (fixtures.POOR_AIR_PM10, "pm10"),
        (fixtures.CLEAR_HIGH_UV, "uv_index"),
    ],
)
def test_boundary_fixtures_match_configured_thresholds(context, field_name: str):
    assert getattr(context, field_name) == BY_FIELD[field_name].value


def _write_config(path: Path, payload: dict) -> Path:
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_unknown_field_raises(tmp_path: Path):
    bad_config = _write_config(
        tmp_path / "bad.json",
        {"humidity": {"value": 80.0, "effect": DEPRIORITISE, "message": "x", "source": "y"}},
    )
    with pytest.raises(ValueError, match="not a field on Context"):
        load_thresholds(bad_config)


def test_unknown_effect_raises(tmp_path: Path):
    bad_config = _write_config(
        tmp_path / "bad.json",
        {"precip_prob": {"value": 0.6, "effect": "exclude", "message": "x", "source": "y"}},
    )
    with pytest.raises(ValueError, match="Must be one of"):
        load_thresholds(bad_config)