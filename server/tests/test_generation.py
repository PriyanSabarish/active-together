from __future__ import annotations

import json

from app.missions.generation import generate_missions
from app.missions.models import Band, MissionTemplate, Review, TemplateStep
from app.model_client import FixtureModelClient
from app.models import AgeBand
from tests import fixtures

PLACE_PLAYGROUND = fixtures.DENSE_INNER[1]  # Lincoln Square Playground


class RaisingModelClient:
    """Fails the test loudly if generate_text is ever called."""

    def generate_text(self, prompt: str, max_tokens: int, timeout_s: int) -> str | None:
        raise AssertionError("generate_text should not have been called")


def _step(sequence: int, prompt_text: str = "Hop to the fence.", variable: bool = True):
    return TemplateStep(sequence=sequence, prompt_text=prompt_text, verify_mode="self", prompt_id=None, variable=variable)


def _template(**overrides):
    defaults = dict(
        template_id="fx_gen_test",
        title="Generation test",
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


def _rewrite_json(texts: dict[int, str]) -> str:
    return json.dumps({"steps": [{"sequence": seq, "prompt_text": text} for seq, text in texts.items()]})


def test_no_model_client_serves_library_direct():
    template = _template()
    missions = generate_missions([template], PLACE_PLAYGROUND, fixtures.CLEAR_MILD, AgeBand.BAND_5_7, 20)
    assert len(missions) == 1
    assert missions[0].template_id == "fx_gen_test"
    assert missions[0].steps[0].prompt_text == "Hop to the fence."


def test_valid_generation_rewrites_variable_steps():
    template = _template()
    rewritten = _rewrite_json({1: "Rewritten one.", 2: "Rewritten two.", 3: "Rewritten three."})
    client = FixtureModelClient(default_text=rewritten)

    missions = generate_missions(
        [template], PLACE_PLAYGROUND, fixtures.CLEAR_MILD, AgeBand.BAND_5_7, 20, model_client=client,
    )
    assert len(missions) == 1
    assert [s.prompt_text for s in missions[0].steps] == ["Rewritten one.", "Rewritten two.", "Rewritten three."]


def test_no_variable_steps_never_calls_the_model():
    template = _template(bands={
        AgeBand.BAND_5_7: Band(title=None, steps=[_step(1, variable=False), _step(2, variable=False), _step(3, variable=False)])
    })
    missions = generate_missions(
        [template], PLACE_PLAYGROUND, fixtures.CLEAR_MILD, AgeBand.BAND_5_7, 20, model_client=RaisingModelClient(),
    )
    assert len(missions) == 1
    assert missions[0].steps[0].prompt_text == "Hop to the fence."


def test_generation_returning_none_falls_back_to_library_direct_same_template():
    template = _template()
    client = FixtureModelClient(default_text=None)

    missions = generate_missions(
        [template], PLACE_PLAYGROUND, fixtures.CLEAR_MILD, AgeBand.BAND_5_7, 20, model_client=client,
    )
    assert len(missions) == 1
    assert missions[0].template_id == "fx_gen_test"
    assert missions[0].steps[0].prompt_text == "Hop to the fence."


def test_malformed_json_falls_back_to_library_direct():
    template = _template()
    client = FixtureModelClient(default_text="not valid json")

    missions = generate_missions(
        [template], PLACE_PLAYGROUND, fixtures.CLEAR_MILD, AgeBand.BAND_5_7, 20, model_client=client,
    )
    assert len(missions) == 1
    assert missions[0].steps[0].prompt_text == "Hop to the fence."


def test_missing_steps_key_falls_back_to_library_direct():
    template = _template()
    client = FixtureModelClient(default_text=json.dumps({"unexpected": "shape"}))

    missions = generate_missions(
        [template], PLACE_PLAYGROUND, fixtures.CLEAR_MILD, AgeBand.BAND_5_7, 20, model_client=client,
    )
    assert len(missions) == 1
    assert missions[0].steps[0].prompt_text == "Hop to the fence."


def test_empty_rewritten_text_falls_back_to_library_direct():
    template = _template()
    client = FixtureModelClient(default_text=_rewrite_json({1: "", 2: "Rewritten two.", 3: "Rewritten three."}))

    missions = generate_missions(
        [template], PLACE_PLAYGROUND, fixtures.CLEAR_MILD, AgeBand.BAND_5_7, 20, model_client=client,
    )
    assert len(missions) == 1
    # the whole candidate falls back to library-direct wording, not a partial mix
    assert missions[0].steps[0].prompt_text == "Hop to the fence."


class TitleAwareModelClient:
    """Returns an unsafe rewrite for the 'Unsafe template' prompt and a
    benign one for everything else — distinguishes the two candidates by
    the title embedded in build_generation_prompt's text."""

    def generate_text(self, prompt: str, max_tokens: int, timeout_s: int) -> str | None:
        if "Unsafe template" in prompt:
            return _rewrite_json({1: "Climb the tree over there.", 2: "Wave both arms.", 3: "Walk backwards."})
        return _rewrite_json({1: "Rewritten one.", 2: "Rewritten two.", 3: "Rewritten three."})


def test_unsafe_generated_text_is_rejected_and_moves_to_next_template():
    unsafe = _template(template_id="fx_unsafe", title="Unsafe template")
    safe = _template(template_id="fx_safe", title="Safe template")

    missions = generate_missions(
        [unsafe, safe], PLACE_PLAYGROUND, fixtures.CLEAR_MILD, AgeBand.BAND_5_7, 20,
        model_client=TitleAwareModelClient(),
    )
    template_ids = [m.template_id for m in missions]
    assert "fx_unsafe" not in template_ids
    assert "fx_safe" in template_ids


def test_caps_at_max_missions():
    templates = [_template(template_id=f"fx_{i}") for i in range(5)]
    missions = generate_missions(templates, PLACE_PLAYGROUND, fixtures.CLEAR_MILD, AgeBand.BAND_5_7, 20)
    assert len(missions) == 3


def test_returns_fewer_than_max_when_not_enough_candidates():
    templates = [_template(template_id="fx_only_one")]
    missions = generate_missions(templates, PLACE_PLAYGROUND, fixtures.CLEAR_MILD, AgeBand.BAND_5_7, 20)
    assert len(missions) == 1


def test_returns_empty_list_when_nothing_matches():
    template = _template()
    missions = generate_missions(
        [template], PLACE_PLAYGROUND, fixtures.CLEAR_MILD, AgeBand.BAND_8_10, 20,
    )
    assert missions == []


def test_logs_library_direct_source_when_no_model_client(caplog):
    template = _template()
    with caplog.at_level("INFO"):
        generate_missions([template], PLACE_PLAYGROUND, fixtures.CLEAR_MILD, AgeBand.BAND_5_7, 20)
    assert any("produced by library-direct" in r.message for r in caplog.records)


def test_logs_model_client_class_name_on_successful_generation(caplog):
    template = _template()
    client = FixtureModelClient(default_text=_rewrite_json({1: "a.", 2: "b.", 3: "c."}))
    with caplog.at_level("INFO"):
        generate_missions(
            [template], PLACE_PLAYGROUND, fixtures.CLEAR_MILD, AgeBand.BAND_5_7, 20, model_client=client,
        )
    assert any("produced by FixtureModelClient" in r.message for r in caplog.records)


def test_logs_library_direct_when_generation_falls_back(caplog):
    template = _template()
    client = FixtureModelClient(default_text=None)
    with caplog.at_level("INFO"):
        generate_missions(
            [template], PLACE_PLAYGROUND, fixtures.CLEAR_MILD, AgeBand.BAND_5_7, 20, model_client=client,
        )
    assert any("produced by library-direct" in r.message for r in caplog.records)


def test_preferences_and_recent_ids_still_apply():
    template = _template(category="playground")
    missions = generate_missions(
        [template], PLACE_PLAYGROUND, fixtures.CLEAR_MILD, AgeBand.BAND_5_7, 20,
        preferences=["playground"],
    )
    assert missions == []

    missions = generate_missions(
        [template], PLACE_PLAYGROUND, fixtures.CLEAR_MILD, AgeBand.BAND_5_7, 20,
        recent_template_ids=["fx_gen_test"],
    )
    assert missions == []
