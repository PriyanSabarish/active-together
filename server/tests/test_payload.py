"""Tests for the combo card payload (task B7), story 3.2."""

import pytest

from app.models import ActivityCategory, DURATION_BUCKETS, Place
from app.recommendation.combos import COMBOS, find_combo
from app.recommendation.recommend import recommend
from tests import fixtures


def make_place(**overrides) -> Place:
    defaults = dict(
        place_id="t_001",
        display_name="Test Reserve",
        activity_category=ActivityCategory.PARK_AND_GARDEN,
        lga_name="Melbourne",
        latitude=-37.80,
        longitude=144.96,
        distance_m=500,
        classification_confidence=0.90,
    )
    return Place(**{**defaults, **overrides})


# The template library


def test_every_category_has_a_template_in_every_bucket():
    assert len(COMBOS) == len(ActivityCategory) * len(DURATION_BUCKETS) == 21


def test_template_ids_are_unique():
    ids = [t.template_id for t in COMBOS.values()]
    assert len(set(ids)) == len(ids)


def test_activity_type_is_constant_across_buckets():
    """What the child does does not change with duration, only how long."""
    for category in ActivityCategory:
        types = {find_combo(category, b).activity_type for b in DURATION_BUCKETS}
        assert len(types) == 1


def test_activity_type_differs_from_the_category_label():
    """Story 3.2 lists activity type and category as separate facts."""
    template = find_combo(ActivityCategory.PARK_AND_GARDEN, 40)
    assert template.activity_type != ActivityCategory.PARK_AND_GARDEN.value


def test_title_is_readable_not_an_identifier():
    template = find_combo(ActivityCategory.PARK_AND_GARDEN, 40)
    assert "_" not in template.title
    assert template.title[0].isupper()


# The card payload — story 3.2 first two criteria


def test_card_carries_the_verified_place_facts():
    result = recommend(fixtures.DENSE_INNER, fixtures.CLEAR_MILD, duration_min=45)
    combo = result.combos[0]
    assert combo.place.display_name
    assert combo.place.distance_m > 0
    assert combo.activity_type
    assert combo.environmental_summary is not None


def test_card_carries_duration_bucket_and_combo():
    result = recommend(fixtures.DENSE_INNER, fixtures.CLEAR_MILD, duration_min=45)
    combo = result.combos[0]
    assert combo.entered_duration_min == 45
    assert combo.duration_bucket == 40
    assert combo.combo_template


def test_combo_matches_the_place_category_and_bucket():
    result = recommend(fixtures.MIDDLE_MONASH, fixtures.CLEAR_MILD, duration_min=60)
    for combo in result.combos:
        expected = find_combo(combo.place.activity_category, 60)
        assert combo.combo_template == expected.title
        assert combo.activity_type == expected.activity_type


def test_unnamed_place_still_produces_a_card():
    """Story 1.2 asks for the available name — absence is not an error."""
    result = recommend((make_place(display_name=None),), fixtures.CLEAR_MILD, 45)
    assert len(result.combos) == 1
    assert result.combos[0].place.display_name is None


# Anti-invention — story 3.2 third criterion, and B9 groundwork


def test_no_opening_hours_cost_or_facilities_on_the_payload():
    """Place does not carry them and nothing here infers them."""
    result = recommend(fixtures.DENSE_INNER, fixtures.CLEAR_MILD, duration_min=45)
    combo = result.combos[0]
    forbidden = {"opening_hours", "cost", "price", "facilities", "accessibility"}
    assert not forbidden & set(vars(combo))
    assert not forbidden & set(vars(combo.place))


def test_unavailable_weather_stays_none_on_the_card():
    """Missing values are absent, never filled with a default."""
    result = recommend(fixtures.DENSE_INNER, fixtures.UNAVAILABLE, duration_min=45)
    summary = result.combos[0].environmental_summary
    assert summary.available is False
    assert summary.temp_c is None
    assert summary.precip_prob is None


def test_partial_weather_keeps_present_values_and_omits_the_rest():
    result = recommend(fixtures.DENSE_INNER, fixtures.PARTIAL, duration_min=45)
    summary = result.combos[0].environmental_summary
    assert summary.temp_c == 17.0
    assert summary.wind_gust_kmh is None
    assert summary.uv_index is None