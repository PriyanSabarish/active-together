from __future__ import annotations

from app.models import ActivityCategory
from app.recommendation.preferences import filter_by_preference
from app.recommendation.recommend import recommend
from tests import fixtures


def test_no_exclusions_returns_everything_unchanged():
    result = filter_by_preference(fixtures.DENSE_INNER)
    assert result == fixtures.DENSE_INNER


def test_excludes_matching_category():
    result = filter_by_preference(fixtures.DENSE_INNER, excluded_categories=[ActivityCategory.SPORTS_GROUND])
    assert all(p.activity_category != ActivityCategory.SPORTS_GROUND for p in result)
    assert len(result) < len(fixtures.DENSE_INNER)


def test_leaves_non_excluded_categories_untouched():
    result = filter_by_preference(fixtures.DENSE_INNER, excluded_categories=[ActivityCategory.SPORTS_GROUND])
    assert any(p.activity_category == ActivityCategory.PLAYGROUND for p in result)


def test_relaxes_when_exclusion_would_return_zero():
    # SINGLE_CATEGORY is entirely PARK_AND_GARDEN — excluding it should
    # relax back to the unfiltered set rather than returning nothing.
    result = filter_by_preference(fixtures.SINGLE_CATEGORY, excluded_categories=[ActivityCategory.PARK_AND_GARDEN])
    assert result == fixtures.SINGLE_CATEGORY


def test_excluding_multiple_categories():
    result = filter_by_preference(
        fixtures.DENSE_INNER,
        excluded_categories=[ActivityCategory.SPORTS_GROUND, ActivityCategory.COURT],
    )
    assert all(
        p.activity_category not in (ActivityCategory.SPORTS_GROUND, ActivityCategory.COURT)
        for p in result
    )


def test_empty_places_returns_empty():
    assert filter_by_preference((), excluded_categories=[ActivityCategory.PLAYGROUND]) == ()


#  Integration with recommend()


def test_recommend_excludes_preferred_away_category():
    result = recommend(
        fixtures.DENSE_INNER, fixtures.CLEAR_MILD, duration_min=45,
        excluded_categories=(ActivityCategory.SPORTS_GROUND,),
    )
    assert all(combo.place.activity_category != ActivityCategory.SPORTS_GROUND for combo in result.combos)


def test_recommend_without_excluded_categories_is_unchanged():
    baseline = recommend(fixtures.DENSE_INNER, fixtures.CLEAR_MILD, duration_min=45)
    with_empty_exclusion = recommend(
        fixtures.DENSE_INNER, fixtures.CLEAR_MILD, duration_min=45, excluded_categories=(),
    )
    assert baseline == with_empty_exclusion


def test_recommend_relaxes_when_exclusion_would_empty_results():
    result = recommend(
        fixtures.SINGLE_CATEGORY, fixtures.CLEAR_MILD, duration_min=45,
        excluded_categories=(ActivityCategory.PARK_AND_GARDEN,),
    )
    assert result.status.value == "ok"
    assert len(result.combos) > 0
