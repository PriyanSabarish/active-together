"""Travel time in the decision logic (B49, B50)."""

from __future__ import annotations

import pytest

from app.models import (
    ActivityCategory,
    Place,
    RecommendationStatus,
    SuggestionKind,
    TravelMode,
    TravelTime,
)
from app.recommendation.eligibility import filter_eligible, plan_bucket_for
from app.recommendation.explanation import duration_clause
from app.recommendation.recommend import recommend
from tests import fixtures


def make_place(place_id="t_001", distance_m=500, **overrides) -> Place:
    defaults = dict(
        place_id=place_id,
        display_name=f"Place {place_id}",
        activity_category=ActivityCategory.PARK_AND_GARDEN,
        lga_name="Melbourne",
        latitude=-37.80,
        longitude=144.96,
        distance_m=distance_m,
        classification_confidence=0.90,
    )
    return Place(**{**defaults, **overrides})


def times(**minutes_by_id) -> dict[str, TravelTime]:
    return {pid: TravelTime(minutes=m, source="openrouteservice") for pid, m in minutes_by_id.items()}


# Plan length and the travel block


def test_60_total_10_min_away_gives_40_minute_plan_and_10_40_10_block():
    result = recommend((make_place(),), fixtures.CLEAR_MILD, 60, times(t_001=10))
    combo = result.combos[0]
    assert combo.duration_bucket == 40
    t = combo.travel
    assert (t.out_min, t.on_site_min, t.back_min, t.total_min) == (10, 40, 10, 60)
    assert t.mode is TravelMode.WALKING
    assert t.source == "openrouteservice"
    assert t.back_from_outbound is True


def test_45_total_7_min_each_way_gives_20_minute_plan_not_40():
    combo = recommend((make_place(),), fixtures.CLEAR_MILD, 45, times(t_001=7)).combos[0]
    assert combo.duration_bucket == 20
    assert combo.entered_duration_min == 45
    assert combo.travel.total_min == 7 + 20 + 7


def test_each_combo_carries_its_own_plan_length():
    near = make_place("near", distance_m=300)
    far = make_place("far", distance_m=2500)
    result = recommend((near, far), fixtures.CLEAR_MILD, 60, times(near=5, far=15))
    by_id = {c.combo_id: c for c in result.combos}
    assert by_id["near"].duration_bucket == 40
    assert by_id["far"].duration_bucket == 20
    assert by_id["near"].travel.on_site_min == 40
    assert by_id["far"].travel.on_site_min == 20
    assert by_id["near"].explanation != by_id["far"].explanation


def test_explanation_states_each_places_own_plan_length():
    near = make_place("near", distance_m=300)
    far = make_place("far", distance_m=2500)
    result = recommend((near, far), fixtures.CLEAR_MILD, 60, times(near=5, far=15))
    for c in result.combos:
        assert f"{c.travel.on_site_min} minute plan here" in c.explanation


def test_estimate_source_is_labelled_on_block_and_explanation():
    est = {"t_001": TravelTime(minutes=8, source="estimate")}
    combo = recommend((make_place(),), fixtures.CLEAR_MILD, 60, est).combos[0]
    assert combo.travel.source == "estimate"
    assert "(estimated)" in combo.explanation


def test_routed_source_is_not_labelled_estimated():
    combo = recommend((make_place(),), fixtures.CLEAR_MILD, 60, times(t_001=8)).combos[0]
    assert "(estimated)" not in combo.explanation


def test_mode_is_carried_through():
    combo = recommend(
        (make_place(),), fixtures.CLEAR_MILD, 60, times(t_001=4), mode=TravelMode.CYCLING
    ).combos[0]
    assert combo.travel.mode is TravelMode.CYCLING
    assert "by cycling" in combo.explanation


def test_explanation_quotes_entered_window_and_trip_each_way():
    combo = recommend((make_place(),), fixtures.CLEAR_MILD, 45, times(t_001=7)).combos[0]
    assert duration_clause(45, combo.travel) in combo.explanation
    assert "45 minute window" in combo.explanation
    assert "7 minutes each way" in combo.explanation


# Fit check in eligibility


def test_place_that_cannot_fit_is_excluded():
    close = make_place("close")
    distant = make_place("distant", distance_m=4000)
    result = recommend((close, distant), fixtures.CLEAR_MILD, 45, times(close=5, distant=15))
    assert [c.combo_id for c in result.combos] == ["close"]


def test_exact_fit_is_eligible_and_one_minute_short_is_not():
    place = make_place()
    assert plan_bucket_for(place, 40, times(t_001=10)) == 20
    assert plan_bucket_for(place, 39, times(t_001=10)) is None


def test_place_without_a_travel_time_is_excluded():
    a, b = make_place("a"), make_place("b", distance_m=900)
    result = recommend((a, b), fixtures.CLEAR_MILD, 60, times(a=5))
    assert [c.combo_id for c in result.combos] == ["a"]


def test_filter_eligible_still_applies_basic_checks():
    place = make_place(lga_name="Geelong")
    assert filter_eligible((place,), 3, 60, times(t_001=5)) == ()


# Ordering unchanged (D17)


def test_order_follows_straight_line_distance_not_travel_time():
    near = make_place("near", distance_m=300)
    far = make_place("far", distance_m=900)
    # the nearer place has the longer travel time
    result = recommend((far, near), fixtures.CLEAR_MILD, 80, times(near=12, far=3))
    assert [c.combo_id for c in result.combos] == ["near", "far"]


def test_order_ties_break_on_name():
    a = make_place("b_id", distance_m=500, display_name="Alpha")
    b = make_place("a_id", distance_m=500, display_name="Beta")
    result = recommend((b, a), fixtures.CLEAR_MILD, 60, times(b_id=5, a_id=5))
    assert [c.place.display_name for c in result.combos] == ["Alpha", "Beta"]


def test_cap_of_three_and_no_padding_hold():
    dense = recommend(
        fixtures.DENSE_INNER, fixtures.CLEAR_MILD, 60, fixtures.travel(fixtures.DENSE_INNER)
    )
    assert len(dense.combos) == 3
    sparse = recommend(
        fixtures.SPARSE_OUTER, fixtures.CLEAR_MILD, 60, fixtures.travel(fixtures.SPARSE_OUTER)
    )
    assert len(sparse.combos) == 2


# Zero results and suggestions (B50)


def test_25_min_walking_nothing_fits_gives_both_suggestions():
    result = recommend((make_place(),), fixtures.CLEAR_MILD, 25, times(t_001=10))
    assert result.status is RecommendationStatus.ZERO_RESULTS
    assert result.combos == ()
    more, other = result.suggestions
    assert more.kind is SuggestionKind.MORE_TIME
    assert more.total_min == 10 + 20 + 10
    assert more.fits_count == 1
    assert other.kind is SuggestionKind.OTHER_MODE
    assert other.mode is TravelMode.CYCLING
    assert other.total_min is None and other.fits_count is None


def test_more_time_names_the_nearest_place_and_counts_what_then_fits():
    near = make_place("near", distance_m=300)
    mid = make_place("mid", distance_m=800)
    far = make_place("far", distance_m=2000)
    tt = times(near=10, mid=12, far=30)
    result = recommend((far, mid, near), fixtures.CLEAR_MILD, 30, tt)
    more = result.suggestions[0]
    assert more.total_min == 40  # nearest: 10 + 20 + 10
    assert more.fits_count == 1  # mid needs 44, far needs 80
    assert recommend((far, mid, near), fixtures.CLEAR_MILD, 44, tt).status is RecommendationStatus.OK


def test_suggested_total_really_does_fit_the_nearest_place():
    place = make_place()
    tt = times(t_001=9)
    more = recommend((place,), fixtures.CLEAR_MILD, 20, tt).suggestions[0]
    assert recommend((place,), fixtures.CLEAR_MILD, more.total_min, tt).status is (
        RecommendationStatus.OK
    )
    assert recommend((place,), fixtures.CLEAR_MILD, more.total_min - 1, tt).status is (
        RecommendationStatus.ZERO_RESULTS
    )


def test_more_time_omitted_when_suggested_total_exceeds_the_maximum():
    result = recommend((make_place(),), fixtures.CLEAR_MILD, 60, times(t_001=51))
    assert [s.kind for s in result.suggestions] == [SuggestionKind.OTHER_MODE]


@pytest.mark.parametrize(
    ("mode", "expected"),
    [(TravelMode.WALKING, TravelMode.CYCLING), (TravelMode.CYCLING, TravelMode.DRIVING)],
)
def test_other_mode_is_a_faster_mode(mode, expected):
    result = recommend((make_place(),), fixtures.CLEAR_MILD, 25, times(t_001=10), mode=mode)
    assert result.suggestions[-1].mode is expected


def test_no_other_mode_suggestion_when_already_driving():
    result = recommend(
        (make_place(),), fixtures.CLEAR_MILD, 25, times(t_001=10), mode=TravelMode.DRIVING
    )
    assert [s.kind for s in result.suggestions] == [SuggestionKind.MORE_TIME]


def test_suggestions_never_name_or_count_excluded_places():
    outside = make_place("outside", distance_m=100, lga_name="Geelong")
    skipped = make_place("skipped", distance_m=150, activity_category=ActivityCategory.PLAYGROUND)
    real = make_place("real", distance_m=900)
    tt = times(outside=2, skipped=2, real=15)
    result = recommend(
        (outside, skipped, real),
        fixtures.CLEAR_MILD,
        30,
        tt,
        excluded_categories=(ActivityCategory.PLAYGROUND,),
    )
    more = result.suggestions[0]
    assert more.total_min == 50  # based on "real", not the closer excluded places
    assert more.fits_count == 1


def test_no_candidates_means_no_more_time_suggestion():
    result = recommend((), fixtures.CLEAR_MILD, 60, {})
    assert result.status is RecommendationStatus.ZERO_RESULTS
    assert [s.kind for s in result.suggestions] == [SuggestionKind.OTHER_MODE]


def test_only_excluded_places_gives_no_more_time_suggestion():
    result = recommend((make_place(lga_name="Geelong"),), fixtures.CLEAR_MILD, 60, times(t_001=5))
    assert result.status is RecommendationStatus.ZERO_RESULTS
    assert [s.kind for s in result.suggestions] == [SuggestionKind.OTHER_MODE]
