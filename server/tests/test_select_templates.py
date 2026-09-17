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
    # "any" is eligible for every place, so excluding "playground" leaves
    # a non-empty result and relaxation never kicks in here.
    excluded = _template(template_id="fx_playground", category="playground")
    other = _template(template_id="fx_any", category="any")
    result = select_templates(
        [excluded, other], PLACE_PLAYGROUND, fixtures.CLEAR_MILD, AgeBand.BAND_5_7, 20,
        preferences=["playground"],
    )
    assert result == [other]


def test_preferences_do_not_exclude_other_categories():
    template = _template(category="playground")
    result = select_templates(
        [template], PLACE_PLAYGROUND, fixtures.CLEAR_MILD, AgeBand.BAND_5_7, 20,
        preferences=["sports_ground"],
    )
    assert result == [template]


def test_preference_exclusion_relaxes_when_it_would_return_zero():
    # The only eligible template is also the excluded category — B33's
    # sibling rule for preferences: getting something beats getting
    # nothing because of an exclusion.
    template = _template(category="playground")
    result = select_templates(
        [template], PLACE_PLAYGROUND, fixtures.CLEAR_MILD, AgeBand.BAND_5_7, 20,
        preferences=["playground"],
    )
    assert result == [template]


def test_recent_template_ids_excludes_by_id():
    recent = _template(template_id="fx_recently_served")
    other = _template(template_id="fx_fresh")
    result = select_templates(
        [recent, other], PLACE_PLAYGROUND, fixtures.CLEAR_MILD, AgeBand.BAND_5_7, 20,
        recent_template_ids=["fx_recently_served"],
    )
    assert result == [other]


def test_recent_template_ids_relaxes_when_it_would_return_zero():
    # B33: the only eligible template was also just served — relax rather
    # than return nothing.
    template = _template(template_id="fx_recently_served")
    result = select_templates(
        [template], PLACE_PLAYGROUND, fixtures.CLEAR_MILD, AgeBand.BAND_5_7, 20,
        recent_template_ids=["fx_recently_served"],
    )
    assert result == [template]


def test_recent_exclusion_relaxes_against_the_preference_stage_output_not_the_original_pool():
    # A: excluded by preference. B: not excluded by preference, but is
    # "recent". Recency relaxation must fall back to what preference
    # filtering left (just B) — never bring A back.
    excluded_by_preference = _template(template_id="fx_a", category="playground")
    recent = _template(template_id="fx_b", category="any")

    result = select_templates(
        [excluded_by_preference, recent], PLACE_PLAYGROUND, fixtures.CLEAR_MILD, AgeBand.BAND_5_7, 20,
        preferences=["playground"], recent_template_ids=["fx_b"],
    )
    assert result == [recent]


def test_relaxation_never_reintroduces_a_hard_filter_failure():
    wrong_band = _template(template_id="fx_wrong_band", bands={AgeBand.BAND_11_12: Band(title=None, steps=[_step()])})
    result = select_templates(
        [wrong_band], PLACE_PLAYGROUND, fixtures.CLEAR_MILD, AgeBand.BAND_5_7, 20,
        preferences=["playground"], recent_template_ids=["fx_wrong_band"],
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


#  eligible_categories (B20 follow-up): the real per-place-type binding for
#  "any"-category templates, from content/taxonomy/mission_context_bindings.yaml


def test_any_category_with_no_binding_matches_everywhere():
    template = _template(category="any", template_id="fx_unbound")
    result = select_templates(
        [template], PLACE_SPORTS_GROUND, fixtures.CLEAR_MILD, AgeBand.BAND_5_7, 20,
        eligible_categories={},
    )
    assert result == [template]


def test_any_category_with_binding_excludes_place_not_on_the_shortlist():
    template = _template(category="any", template_id="fx_bound")
    result = select_templates(
        [template], PLACE_SPORTS_GROUND, fixtures.CLEAR_MILD, AgeBand.BAND_5_7, 20,
        eligible_categories={"fx_bound": ["playground", "park_and_garden"]},
    )
    assert result == []


def test_any_category_with_binding_matches_place_on_the_shortlist():
    template = _template(category="any", template_id="fx_bound")
    result = select_templates(
        [template], PLACE_PLAYGROUND, fixtures.CLEAR_MILD, AgeBand.BAND_5_7, 20,
        eligible_categories={"fx_bound": ["playground", "park_and_garden"]},
    )
    assert result == [template]


def test_binding_with_empty_list_is_treated_as_unbound():
    template = _template(category="any", template_id="fx_empty_binding")
    result = select_templates(
        [template], PLACE_SPORTS_GROUND, fixtures.CLEAR_MILD, AgeBand.BAND_5_7, 20,
        eligible_categories={"fx_empty_binding": []},
    )
    assert result == [template]


def test_binding_never_applies_to_non_any_categories():
    # A binding entry for a template that has a specific (non-"any") category
    # is irrelevant — the direct category==place rule still governs.
    template = _template(category="playground", template_id="fx_specific")
    result = select_templates(
        [template], PLACE_SPORTS_GROUND, fixtures.CLEAR_MILD, AgeBand.BAND_5_7, 20,
        eligible_categories={"fx_specific": ["sports_ground"]},
    )
    assert result == []


def test_against_the_real_reviewed_library_and_bindings():
    from app.missions.context_bindings import load_eligible_categories
    from app.missions.loader import load_template_dir

    templates = load_template_dir()
    bindings = load_eligible_categories()

    colour_hunt_at_playground = select_templates(
        templates, PLACE_PLAYGROUND, fixtures.CLEAR_MILD, AgeBand.BAND_5_7, 20,
        eligible_categories=bindings,
    )
    assert any(t.template_id == "activity_colour_hunt" for t in colour_hunt_at_playground)

    colour_hunt_at_sports_ground = select_templates(
        templates, PLACE_SPORTS_GROUND, fixtures.CLEAR_MILD, AgeBand.BAND_5_7, 20,
        eligible_categories=bindings,
    )
    assert not any(t.template_id == "activity_colour_hunt" for t in colour_hunt_at_sports_ground)
