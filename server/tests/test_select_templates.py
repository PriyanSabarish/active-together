from __future__ import annotations

import pytest

from app.missions.models import Band, MissionTemplate, Review, TemplateStep
from app.missions.selector import select_templates
from app.models import ActivityCategory, AgeBand, Context, Place
from tests import fixtures
from tests import mission_fixtures as mfx

PLACE_PLAYGROUND = fixtures.DENSE_INNER[1]  # Lincoln Square Playground
PLACE_PARK = fixtures.DENSE_INNER[0]  # Argyle Square, park_and_garden
PLACE_SPORTS_GROUND = fixtures.DENSE_INNER[3]  # Princes Park Oval


def _step(sequence=1, **overrides):
    defaults = dict(prompt_text=f"Step {sequence}.", verify_mode="self", prompt_id=None, variable=True)
    return TemplateStep(sequence=sequence, **{**defaults, **overrides})


def _template(**overrides):
    defaults = dict(
        template_id="fx_test_template",
        title="Test template",
        category="playground",
        duration_bucket=20,
        weather_tags=["any"],
        site_requirements=["grass"],
        equipment=[],
        mechanic="move",
        bands={AgeBand.BAND_5_7: Band(title=None, steps=[_step()])},
        safety_tags=["inherited"],
        review=Review(author="fixture", reviewed_by=None, status="draft"),
    )
    return MissionTemplate(**{**defaults, **overrides})


def test_matches_place_category():
    template = _template(category="playground")
    result = select_templates([template], PLACE_PLAYGROUND, fixtures.CLEAR_MILD, AgeBand.BAND_5_7, 20)
    assert result == [template]


def test_excludes_mismatched_category():
    template = _template(category="sports_ground")
    result = select_templates([template], PLACE_PLAYGROUND, fixtures.CLEAR_MILD, AgeBand.BAND_5_7, 20)
    assert result == []


def test_any_category_matches_every_place():
    template = _template(category="any")
    for place in (PLACE_PLAYGROUND, PLACE_PARK, PLACE_SPORTS_GROUND):
        assert select_templates([template], place, fixtures.CLEAR_MILD, AgeBand.BAND_5_7, 20) == [template]


def test_excludes_missing_age_band():
    template = _template(bands={AgeBand.BAND_11_12: Band(title=None, steps=[_step()])})
    result = select_templates([template], PLACE_PLAYGROUND, fixtures.CLEAR_MILD, AgeBand.BAND_5_7, 20)
    assert result == []


def test_bucket_shorter_than_requested_is_excluded():
    template = _template(duration_bucket=20)
    result = select_templates([template], PLACE_PLAYGROUND, fixtures.CLEAR_MILD, AgeBand.BAND_5_7, 40)
    assert result == []


def test_longer_family_covers_a_shorter_request():
    template = _template(duration_bucket=60, bands={
        AgeBand.BAND_5_7: Band(title=None, steps=[_step(i) for i in range(1, 8)])
    })
    result = select_templates([template], PLACE_PLAYGROUND, fixtures.CLEAR_MILD, AgeBand.BAND_5_7, 20)
    assert result == [template]


def test_wet_only_template_excluded_in_dry_weather():
    template = _template(weather_tags=["wet"])
    result = select_templates([template], PLACE_PLAYGROUND, fixtures.CLEAR_MILD, AgeBand.BAND_5_7, 20)
    assert result == []


def test_wet_only_template_included_when_raining():
    template = _template(weather_tags=["wet"])
    result = select_templates([template], PLACE_PLAYGROUND, fixtures.RAIN_HEAVY, AgeBand.BAND_5_7, 20)
    assert result == [template]


def test_any_weather_tag_always_matches():
    template = _template(weather_tags=["any"])
    result = select_templates([template], PLACE_PLAYGROUND, fixtures.RAIN_HEAVY, AgeBand.BAND_5_7, 20)
    assert result == [template]


def test_preference_exclusion_removes_matching_category():
    template = _template(category="playground")
    result = select_templates(
        [template], PLACE_PLAYGROUND, fixtures.CLEAR_MILD, AgeBand.BAND_5_7, 20,
        preferences=["playground"],
    )
    assert result == []


def test_preferences_do_not_exclude_other_categories():
    template = _template(category="playground")
    result = select_templates(
        [template], PLACE_PLAYGROUND, fixtures.CLEAR_MILD, AgeBand.BAND_5_7, 20,
        preferences=["sports_ground"],
    )
    assert result == [template]


def test_recent_template_ids_excludes_by_id():
    template = _template(template_id="fx_recently_served")
    result = select_templates(
        [template], PLACE_PLAYGROUND, fixtures.CLEAR_MILD, AgeBand.BAND_5_7, 20,
        recent_template_ids=["fx_recently_served"],
    )
    assert result == []


def test_invalid_duration_bucket_raises():
    with pytest.raises(ValueError, match="duration_bucket must be one of"):
        select_templates([_template()], PLACE_PLAYGROUND, fixtures.CLEAR_MILD, AgeBand.BAND_5_7, 30)


def test_against_the_shared_fixture_library():
    # Sanity check against tests/mission_fixtures.py rather than ad-hoc templates.
    result = select_templates(
        mfx.TEMPLATES, PLACE_PLAYGROUND, fixtures.CLEAR_MILD, AgeBand.BAND_5_7, 20,
    )
    ids = {t.template_id for t in result}
    assert ids == {mfx.BUCKET20_BAND_5_7_SELF.template_id, mfx.BARE_SITE_ANY_CATEGORY.template_id}
