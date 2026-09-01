from __future__ import annotations

import pytest

from app.models import DURATION_BUCKETS, ActivityCategory, Place
from app.recommendation.combos import COMBOS, find_combo
from app.recommendation.eligibility import filter_eligible, is_eligible
from tests import fixtures


def make_place(**overrides) -> Place:
    defaults = {
        "place_id": "t_001",
        "display_name": "Test Reserve",
        "activity_category": ActivityCategory.PARK_AND_GARDEN,
        "lga_name": "Melbourne",
        "latitude": -37.80,
        "longitude": 144.96,
        "distance_m": 500,
        "classification_confidence": 0.90,
    }
    return Place(**{**defaults, **overrides})


def test_combo_template_full_coverage():
    expected_count = len(ActivityCategory) * len(DURATION_BUCKETS)
    assert len(COMBOS) == expected_count == 21
    for category in ActivityCategory:
        for bucket in DURATION_BUCKETS:
            assert find_combo(category, bucket) is not None


def test_find_combo_invalid_bucket_returns_none():
    assert find_combo(ActivityCategory.PLAYGROUND, 35) is None


def test_eligible_candidate_passes():
    assert is_eligible(make_place(), radius_km=3, bucket=40)


@pytest.mark.parametrize("lga_name", ["Melbourne", "Melton", "Monash"])
def test_all_pilot_lgas_accepted(lga_name: str):
    assert is_eligible(make_place(lga_name=lga_name), radius_km=3, bucket=40)


def test_non_pilot_lga_rejected():
    assert not is_eligible(make_place(lga_name="Geelong"), radius_km=3, bucket=40)


def test_candidate_outside_radius_rejected():
    assert not is_eligible(make_place(distance_m=3001), radius_km=3, bucket=40)


def test_candidate_on_radius_boundary_accepted():
    assert is_eligible(make_place(distance_m=3000), radius_km=3, bucket=40)


def test_low_confidence_accepted_by_default():
    assert is_eligible(make_place(classification_confidence=0.31), radius_km=3, bucket=40)


def test_low_confidence_filtered_when_threshold_specified():
    place = make_place(classification_confidence=0.31)
    assert not is_eligible(place, radius_km=3, bucket=40, min_confidence=0.70)


def test_filter_dense_inner_places_within_ten_km():
    eligible = filter_eligible(fixtures.DENSE_INNER, radius_km=10, duration_min=45)
    assert len(eligible) == len(fixtures.DENSE_INNER)


def test_filter_dense_inner_places_radius_constrains_results():
    eligible = filter_eligible(fixtures.DENSE_INNER, radius_km=1, duration_min=45)
    assert all(p.distance_m <= 1000 for p in eligible)
    assert len(eligible) < len(fixtures.DENSE_INNER)


def test_filter_empty_place_set():
    assert filter_eligible(fixtures.EMPTY, radius_km=3, duration_min=45) == ()


def test_filter_suppresses_low_confidence_set():
    eligible = filter_eligible(
        fixtures.LOW_CONFIDENCE, radius_km=3, duration_min=45, min_confidence=0.70
    )
    assert eligible == ()


def test_filter_preserves_input_sequence():
    eligible = filter_eligible(fixtures.DENSE_INNER, radius_km=10, duration_min=45)
    assert [p.place_id for p in eligible] == [p.place_id for p in fixtures.DENSE_INNER]


def test_duration_bucket_resolution_propagates_to_combo_lookup():
    eligible = filter_eligible(fixtures.MIDDLE_MONASH, radius_km=10, duration_min=50)
    assert len(eligible) == len(fixtures.MIDDLE_MONASH)