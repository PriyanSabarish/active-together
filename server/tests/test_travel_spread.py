"""
Spread ranking: the top three are spread across the travel limit and across
activity kinds, with "nearest" kept as the exact old behaviour.
"""

from __future__ import annotations

from app.models import ActivityCategory as C, Tier, TravelTime
from app.recommendation.ordering import (
    band_edges,
    band_of,
    pick_varied,
    select_nearest,
    select_spread,
    sort_key,
)
from app.recommendation.recommend import recommend
from tests import fixtures
from tests.test_ordering import make_place

PARK, OVAL, PLAY = C.PARK_AND_GARDEN, C.SPORTS_GROUND, C.PLAYGROUND


def place(pid, dist, cat=PARK, name=None):
    return make_place(pid, dist, display_name=name or pid, activity_category=cat)


def mins(**kw):
    return kw


def spread(places, travel, limit=30, **kw):
    return [p.place_id for p in select_spread(tuple(places), Tier.NORMAL, travel, limit, **kw)]


# --- bands ------------------------------------------------------------------


def test_band_edges_for_each_limit():
    assert band_edges(30, 3) == [(0, 10), (10, 20), (20, 30)]
    assert band_edges(15, 3) == [(0, 5), (5, 10), (10, 15)]
    assert band_edges(10, 3)[0][1] == 10 / 3
    assert band_edges(5, 3)[2][1] == 5


def test_band_of_edge_goes_to_lower_band():
    edges = band_edges(30, 3)
    assert band_of(10, edges) == 0
    assert band_of(10.01, edges) == 1
    assert band_of(20, edges) == 1
    assert band_of(30, edges) == 2


# --- pick_varied ------------------------------------------------------------


def test_pick_varied_prefers_unseen_category():
    pool = [place("a", 100, PARK), place("b", 200, OVAL)]
    assert pick_varied(pool, Tier.NORMAL, {PARK}).place_id == "b"


def test_pick_varied_falls_back_to_nearest_when_all_seen():
    pool = [place("b", 200, OVAL), place("a", 100, PARK)]
    assert pick_varied(pool, Tier.NORMAL, {PARK, OVAL}).place_id == "a"


def test_pick_varied_empty_pool():
    assert pick_varied([], Tier.NORMAL, set()) is None


# --- select_spread ----------------------------------------------------------


WORKED = [
    place("parkA", 400, PARK), place("parkB", 600, PARK), place("playC", 800, PLAY),
    place("parkD", 1200, PARK), place("ovalE", 1500, OVAL),
    place("parkF", 2200, PARK),
]
WORKED_TIME = {"parkA": 4, "parkB": 6, "playC": 8, "parkD": 12, "ovalE": 15, "parkF": 22}


def test_worked_example_reproduces():
    assert spread(WORKED, WORKED_TIME) == ["parkA", "ovalE", "parkF"]


def test_one_result_per_band_in_dense_area():
    places = [place(f"p{i}", i * 100) for i in range(1, 10)]
    travel = {f"p{i}": i * 3 for i in range(1, 10)}  # 3..27 min
    chosen = select_spread(tuple(places), Tier.NORMAL, travel, 30)
    bands = sorted(band_of(travel[p.place_id], band_edges(30, 3)) for p in chosen)
    assert bands == [0, 1, 2]


def test_empty_middle_band_backfills_with_nearest_leftover():
    places = [place("a", 100), place("b", 200), place("c", 300), place("d", 2000)]
    travel = {"a": 2, "b": 4, "c": 6, "d": 25}
    assert spread(places, travel) == ["a", "b", "d"]


def test_fewer_than_three_returns_all_without_padding():
    places = [place("b", 200), place("a", 100)]
    assert spread(places, {"a": 3, "b": 20}) == ["a", "b"]


def test_all_same_category_still_spreads_by_distance():
    places = [place("a", 100), place("b", 200), place("c", 1200), place("d", 2200)]
    travel = {"a": 2, "b": 4, "c": 15, "d": 25}
    assert spread(places, travel) == ["a", "c", "d"]


def test_band_beats_category():
    # The only far-band candidate repeats a category and is still picked.
    places = [place("a", 100, PARK), place("b", 1200, OVAL), place("c", 2200, PARK), place("d", 150, PLAY)]
    travel = {"a": 2, "b": 15, "c": 25, "d": 3}
    assert spread(places, travel) == ["a", "b", "c"]


def test_category_variety_picks_oval_over_nearer_park():
    places = [place("a", 100, PARK), place("park2", 1200, PARK), place("oval", 1500, OVAL), place("far", 2200, PARK)]
    travel = {"a": 2, "park2": 12, "oval": 15, "far": 25}
    assert spread(places, travel) == ["a", "oval", "far"]


def test_small_limit_picks_nearest_of_each_category():
    places = [place("p1", 100, PARK), place("p2", 150, PARK), place("o1", 300, OVAL), place("g1", 400, PLAY)]
    travel = {"p1": 1, "p2": 2, "o1": 3, "g1": 4}
    assert spread(places, travel, limit=10) == ["p1", "o1", "g1"]


def test_small_limit_backfills_when_categories_run_out():
    places = [place("p1", 100), place("p2", 150), place("p3", 200), place("o1", 300, OVAL)]
    travel = {"p1": 1, "p2": 2, "p3": 3, "o1": 4}
    assert spread(places, travel, limit=5) == ["p1", "p2", "o1"]


def test_result_is_in_sort_key_order():
    chosen = select_spread(tuple(WORKED), Tier.NORMAL, WORKED_TIME, 30)
    assert list(chosen) == sorted(chosen, key=lambda p: sort_key(p, Tier.NORMAL))


def test_spread_is_deterministic():
    a = select_spread(tuple(WORKED), Tier.NORMAL, WORKED_TIME, 30)
    b = select_spread(tuple(reversed(WORKED)), Tier.NORMAL, WORKED_TIME, 30)
    assert [p.place_id for p in a] == [p.place_id for p in b]


def test_all_deprioritised_still_spreads():
    places = [place("a", 100), place("b", 1200), place("c", 2200), place("d", 150)]
    travel = {"a": 2, "b": 15, "c": 25, "d": 3}
    chosen = select_spread(tuple(places), Tier.DEPRIORITISED, travel, 30)
    assert [p.place_id for p in chosen] == ["a", "b", "c"]


# --- recommend() ------------------------------------------------------------


def _varied_travel(places, minutes):
    return {p.place_id: TravelTime(minutes=m, source="estimate") for p, m in zip(places, minutes)}


def test_nearest_mode_matches_old_behaviour():
    places = fixtures.DENSE_INNER
    old = recommend(places, fixtures.CLEAR_MILD, 55, fixtures.travel(places))
    nearest = recommend(places, fixtures.CLEAR_MILD, 55, fixtures.travel(places), travel_limit_min=30, ranking_mode="nearest")
    assert [c.place.place_id for c in nearest.combos] == [c.place.place_id for c in old.combos]
    assert nearest.ranking_mode == "nearest"


def test_spread_without_limit_falls_back_to_nearest_and_says_so():
    places = fixtures.DENSE_INNER
    result = recommend(places, fixtures.CLEAR_MILD, 55, fixtures.travel(places), ranking_mode="spread")
    assert result.ranking_mode == "nearest"


def test_recommend_spread_changes_top_three_and_echoes_mode():
    places = tuple(place(f"s{i}", i * 400, PARK) for i in range(1, 9))
    travel = _varied_travel(places, [2, 4, 6, 12, 15, 18, 22, 27])
    near = recommend(places, fixtures.CLEAR_MILD, 120, travel, travel_limit_min=30, ranking_mode="nearest")
    mixed = recommend(places, fixtures.CLEAR_MILD, 120, travel, travel_limit_min=30, ranking_mode="spread")
    assert mixed.ranking_mode == "spread"
    assert [c.place.place_id for c in near.combos] == ["s1", "s2", "s3"]
    assert [c.travel_min for c in mixed.combos] == [2, 12, 22]


def test_spread_does_not_pick_places_past_the_travel_limit():
    places = tuple(place(f"s{i}", i * 400, PARK) for i in range(1, 6))
    travel = _varied_travel(places, [2, 4, 6, 20, 25])
    result = recommend(places, fixtures.CLEAR_MILD, 120, travel, travel_limit_min=10, ranking_mode="spread")
    assert all(c.travel_min <= 10 for c in result.combos)


def test_filter_and_banding_use_the_same_travel_minutes():
    places = tuple(place(f"s{i}", i * 400, PARK) for i in range(1, 7))
    travel = _varied_travel(places, [3, 7, 11, 14, 19, 28])
    result = recommend(places, fixtures.CLEAR_MILD, 120, travel, travel_limit_min=30, ranking_mode="spread")
    assert all(c.travel_min == travel[c.place.place_id].minutes for c in result.combos)
