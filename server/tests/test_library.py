from __future__ import annotations

from app.missions.library import serve_from_library
from app.missions.models import Band, MissionTemplate, Review, TemplateStep
from app.models import AgeBand
from tests import fixtures
from tests import mission_fixtures as mfx

PLACE_PLAYGROUND = fixtures.DENSE_INNER[1]  # Lincoln Square Playground


def _step(sequence: int, prompt_text: str = "Hop to the fence."):
    return TemplateStep(sequence=sequence, prompt_text=prompt_text, verify_mode="self", prompt_id=None, variable=True)


def _template(**overrides):
    defaults = dict(
        template_id="fx_library_test",
        title="Library test",
        category="playground",
        duration_bucket=20,
        weather_tags=["any"],
        site_requirements=["grass"],
        equipment=[],
        mechanic="move",
        bands={AgeBand.BAND_5_7: Band(title=None, steps=[_step(1), _step(2), _step(3)])},
        safety_tags=["inherited"],
        review=Review(author="fixture", reviewed_by=None, status="draft"),
    )
    return MissionTemplate(**{**defaults, **overrides})


def test_returns_a_mission_from_the_real_fixture_library():
    mission = serve_from_library(mfx.TEMPLATES, PLACE_PLAYGROUND, fixtures.CLEAR_MILD, AgeBand.BAND_5_7, 20)
    assert mission is not None
    assert mission.template_id in {mfx.BUCKET20_BAND_5_7_SELF.template_id, mfx.BARE_SITE_ANY_CATEGORY.template_id}
    assert len(mission.steps) == 3


def test_returns_none_when_nothing_matches():
    mission = serve_from_library(mfx.TEMPLATES, PLACE_PLAYGROUND, fixtures.CLEAR_MILD, AgeBand.BAND_8_10, 20)
    assert mission is None


def test_skips_template_that_fails_schema_validation():
    # duration_bucket 40 needs 5 steps; this band only has 3 — invalid.
    bad = _template(duration_bucket=40)
    mission = serve_from_library([bad], PLACE_PLAYGROUND, fixtures.CLEAR_MILD, AgeBand.BAND_5_7, 20)
    assert mission is None


def test_falls_through_to_next_candidate_when_first_fails_safety():
    unsafe = _template(
        template_id="fx_unsafe",
        bands={AgeBand.BAND_5_7: Band(title=None, steps=[
            _step(1, "Climb the tree over there."), _step(2), _step(3),
        ])},
    )
    safe = _template(template_id="fx_safe")

    mission = serve_from_library([unsafe, safe], PLACE_PLAYGROUND, fixtures.CLEAR_MILD, AgeBand.BAND_5_7, 20)
    assert mission is not None
    assert mission.template_id == "fx_safe"


def test_returns_none_when_only_candidate_fails_safety():
    unsafe = _template(
        bands={AgeBand.BAND_5_7: Band(title=None, steps=[
            _step(1, "Cross the road to the other side."), _step(2), _step(3),
        ])},
    )
    mission = serve_from_library([unsafe], PLACE_PLAYGROUND, fixtures.CLEAR_MILD, AgeBand.BAND_5_7, 20)
    assert mission is None


def test_preferences_relax_when_the_only_candidate_would_otherwise_be_excluded():
    # select_templates (B33) relaxes preference/recency exclusion rather
    # than return nothing when it's the only eligible candidate — getting
    # something beats getting nothing because of a soft exclusion.
    template = _template(category="playground")
    mission = serve_from_library(
        [template], PLACE_PLAYGROUND, fixtures.CLEAR_MILD, AgeBand.BAND_5_7, 20,
        preferences=["playground"],
    )
    assert mission is not None
    assert mission.template_id == template.template_id


def test_recent_template_ids_relax_when_the_only_candidate_would_otherwise_be_excluded():
    template = _template(template_id="fx_recent")
    mission = serve_from_library(
        [template], PLACE_PLAYGROUND, fixtures.CLEAR_MILD, AgeBand.BAND_5_7, 20,
        recent_template_ids=["fx_recent"],
    )
    assert mission is not None
    assert mission.template_id == "fx_recent"


def test_empty_template_pool_returns_none():
    mission = serve_from_library([], PLACE_PLAYGROUND, fixtures.CLEAR_MILD, AgeBand.BAND_5_7, 20)
    assert mission is None
