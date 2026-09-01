"""
Unit and integration tests for candidate ordering and recommendation assembly.
"""

from __future__ import annotations

import pytest

from app.models import ActivityCategory, Place, RecommendationStatus, Tier
from app.recommendation.ordering import MAX_COMBOS, order_candidates
from app.recommendation.recommend import recommend
from tests import fixtures


def make_place(
    place_id: str,
    distance_m: int,
    display_name: str | None = "Place",
    **overrides,
) -> Place:
    defaults = {
        "place_id": place_id,
        "display_name": display_name,
        "activity_category": ActivityCategory.PARK_AND_GARDEN,
        "lga_name": "Melbourne",
        "latitude": -37.80,
        "longitude": 144.96,
        "distance_m": distance_m,
        "classification_confidence": 0.90,
    }
    return Place(**{**defaults, **overrides})


def test_order_by_distance_within_same_tier():
    places = (
        make_place("c", 900),
        make_place("a", 100),
        make_place("b", 500),
    )
    ordered = order_candidates(places, Tier.NORMAL)
    assert [p.distance_m for p in ordered] == [100, 500, 900]


def test_order_falls_back_to_name_when_distance_is_equal():
    places = (
        make_place("z", 500, display_name="Zebra Park"),
        make_place("a", 500, display_name="Alpha Park"),
    )
    ordered = order_candidates(places, Tier.NORMAL)
    assert [p.display_name for p in ordered] == ["Alpha Park", "Zebra Park"]


def test_order_by_name_is_case_insensitive():
    places = (
        make_place("b", 500, display_name="beta park"),
        make_place("a", 500, display_name="Alpha Park"),
    )
    ordered = order_candidates(places, Tier.NORMAL)
    assert ordered[0].display_name == "Alpha Park"


def test_unnamed_places_sort_after_named_places_at_same_distance():
    places = (
        make_place("x", 500, display_name=None),
        make_place("y", 500, display_name="Zebra Park"),
    )
    ordered = order_candidates(places, Tier.NORMAL)
    assert ordered[0].display_name == "Zebra Park"
    assert ordered[1].display_name is None


def test_unnamed_places_at_same_distance_use_place_id_tiebreak():
    places = (
        make_place("second", 500, display_name=None),
        make_place("first", 500, display_name=None),
    )
    ordered = order_candidates(places, Tier.NORMAL)
    assert [p.place_id for p in ordered] == ["first", "second"]


def test_order_candidates_caps_at_max_combos():
    places = tuple(make_place(f"p{i}", i * 100) for i in range(1, 8))
    assert len(order_candidates(places, Tier.NORMAL)) == MAX_COMBOS


def test_order_candidates_handles_fewer_than_max():
    places = (make_place("a", 100), make_place("b", 200))
    assert len(order_candidates(places, Tier.NORMAL)) == 2


def test_order_candidates_empty_input():
    assert order_candidates((), Tier.NORMAL) == ()


def test_ordering_is_deterministic():
    first = order_candidates(fixtures.DENSE_INNER, Tier.NORMAL)
    second = order_candidates(fixtures.DENSE_INNER, Tier.NORMAL)
    assert [p.place_id for p in first] == [p.place_id for p in second]


def test_recommend_returns_normal_tier_combos_for_clear_weather():
    result = recommend(fixtures.DENSE_INNER, fixtures.CLEAR_MILD, duration_min=45)
    assert result.status is RecommendationStatus.OK
    assert len(result.combos) == 3
    assert all(c.tier is Tier.NORMAL for c in result.combos)


def test_recommend_orders_closest_first():
    result = recommend(fixtures.DENSE_INNER, fixtures.CLEAR_MILD, duration_min=45)
    assert result.combos[0].place.place_id == "fx_001"


def test_recommend_deprioritises_combos_in_heavy_rain():
    result = recommend(fixtures.DENSE_INNER, fixtures.RAIN_HEAVY, duration_min=45)
    assert all(c.tier is Tier.DEPRIORITISED for c in result.combos)
    assert all(c.environmental_summary.warnings for c in result.combos)


def test_recommend_preserves_exact_count_for_sparse_results():
    result = recommend(fixtures.SPARSE_OUTER, fixtures.CLEAR_MILD, duration_min=45)
    assert len(result.combos) == 2


def test_recommend_retains_entered_duration_and_matched_bucket():
    result = recommend(fixtures.DENSE_INNER, fixtures.CLEAR_MILD, duration_min=50)
    combo = result.combos[0]
    assert combo.entered_duration_min == 50
    assert combo.duration_bucket == 40


def test_recommend_populates_combo_template():
    result = recommend(fixtures.MIDDLE_MONASH, fixtures.CLEAR_MILD, duration_min=60)
    assert all(c.combo_template for c in result.combos)


def test_recommend_handles_unavailable_weather_gracefully():
    result = recommend(fixtures.DENSE_INNER, fixtures.UNAVAILABLE, duration_min=45)
    assert len(result.combos) == 3
    assert all(c.environmental_summary.available is False for c in result.combos)
    assert all(c.tier is Tier.NORMAL for c in result.combos)


def test_recommend_constrains_places_by_radius():
    result = recommend(
        fixtures.DENSE_INNER, fixtures.CLEAR_MILD, duration_min=45, radius_km=1
    )
    assert all(c.place.distance_m <= 1000 for c in result.combos)


def test_recommend_empty_candidate_set():
    result = recommend(fixtures.EMPTY, fixtures.CLEAR_MILD, duration_min=45)
    assert result.combos == ()