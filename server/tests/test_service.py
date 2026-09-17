from __future__ import annotations

import json

from app.missions import service
from app.model_client import FixtureModelClient
from app.models import AgeBand
from tests import fixtures

PLACE_PARK = fixtures.DENSE_INNER[0]  # Argyle Square, park_and_garden


def test_templates_loaded_from_the_real_reviewed_library():
    assert len(service.TEMPLATES) == 18


def test_eligible_categories_loaded_from_the_real_bindings_file():
    assert len(service.ELIGIBLE_CATEGORIES) == 18


def test_get_missions_pure_library_direct():
    # model_client=None explicitly — never hit the real API from the suite,
    # regardless of what GEMINI_API_KEY is set to in this environment.
    missions = service.get_missions(
        PLACE_PARK, fixtures.CLEAR_MILD, AgeBand.BAND_5_7, 20, model_client=None,
    )
    assert missions
    assert all(m.age_band == AgeBand.BAND_5_7 for m in missions)
    assert all(len(m.steps) == 3 for m in missions)  # STEPS_FOR[20]


def test_get_missions_returns_a_real_reviewed_family():
    missions = service.get_missions(
        PLACE_PARK, fixtures.CLEAR_MILD, AgeBand.BAND_5_7, 20, model_client=None,
    )
    assert any(m.template_id == "activity_colour_hunt" for m in missions)


def test_get_missions_respects_recent_template_ids():
    first = service.get_missions(PLACE_PARK, fixtures.CLEAR_MILD, AgeBand.BAND_5_7, 20, model_client=None)
    served_ids = [m.template_id for m in first]

    second = service.get_missions(
        PLACE_PARK, fixtures.CLEAR_MILD, AgeBand.BAND_5_7, 20,
        recent_template_ids=served_ids, model_client=None,
    )
    # 18 real families, only 3 excluded — plenty left, so B33's relaxation
    # should not need to kick in here.
    assert not (set(m.template_id for m in second) & set(served_ids))


def test_get_missions_with_fixture_generation():
    rewritten = json.dumps({"steps": [
        {"sequence": 1, "prompt_text": "one."}, {"sequence": 2, "prompt_text": "two."}, {"sequence": 3, "prompt_text": "three."},
    ]})
    client = FixtureModelClient(default_text=rewritten)

    missions = service.get_missions(
        PLACE_PARK, fixtures.CLEAR_MILD, AgeBand.BAND_5_7, 20, model_client=client,
    )
    assert missions
    assert missions[0].steps[0].prompt_text == "one."


def test_get_missions_uses_the_shared_rejection_stats():
    before = service.REJECTION_STATS.generation_attempts
    rewritten = json.dumps({"steps": [
        {"sequence": 1, "prompt_text": "a."}, {"sequence": 2, "prompt_text": "b."}, {"sequence": 3, "prompt_text": "c."},
    ]})
    service.get_missions(
        PLACE_PARK, fixtures.CLEAR_MILD, AgeBand.BAND_5_7, 20,
        model_client=FixtureModelClient(default_text=rewritten),
    )
    assert service.REJECTION_STATS.generation_attempts > before
