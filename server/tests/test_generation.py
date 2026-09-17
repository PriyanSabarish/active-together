from __future__ import annotations

import json

from app.missions.generation import generate_missions
from app.missions.instrumentation import RejectionStats
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


def test_unsafe_generated_text_is_rejected_and_a_different_template_is_tried_first():
    unsafe = _template(template_id="fx_unsafe", title="Unsafe template")
    safe = _template(template_id="fx_safe", title="Safe template")

    missions = generate_missions(
        [unsafe, safe], PLACE_PLAYGROUND, fixtures.CLEAR_MILD, AgeBand.BAND_5_7, 20,
        model_client=TitleAwareModelClient(),
    )
    # both appear: fx_safe from its own generation, fx_unsafe recovered by
    # B30's retry with its original (safe) library wording — never with
    # the rejected "climb the tree" text.
    by_template = {m.template_id: m for m in missions}
    assert set(by_template) == {"fx_unsafe", "fx_safe"}
    assert by_template["fx_unsafe"].steps[0].prompt_text == "Hop to the fence."
    assert all("climb" not in s.prompt_text.lower() for s in by_template["fx_unsafe"].steps)


#  B30: rejection-path exhaustion


def test_generated_rejection_recovers_with_library_direct_wording():
    unsafe = _template(template_id="fx_unsafe", title="Unsafe template")

    missions = generate_missions(
        [unsafe], PLACE_PLAYGROUND, fixtures.CLEAR_MILD, AgeBand.BAND_5_7, 20,
        model_client=TitleAwareModelClient(),
    )
    assert len(missions) == 1
    assert missions[0].template_id == "fx_unsafe"
    assert missions[0].steps[0].prompt_text == "Hop to the fence."


def test_library_direct_rejection_is_not_retried_and_is_dropped():
    # No model_client at all, so the *library-direct* text is what gets
    # rejected — retrying identical input would just fail identically,
    # so this candidate must not reappear.
    unsafe = _template(bands={
        AgeBand.BAND_5_7: Band(title=None, steps=[
            _step(1, "Cross the road to the other side."), _step(2), _step(3),
        ])
    })

    missions = generate_missions([unsafe], PLACE_PLAYGROUND, fixtures.CLEAR_MILD, AgeBand.BAND_5_7, 20)
    assert missions == []


def test_returns_empty_list_when_every_candidate_is_exhausted():
    # Both the generated AND the library-direct wording are unsafe, so
    # neither the first pass nor B30's retry pass can recover this one.
    def _unsafe_bands():
        return {AgeBand.BAND_5_7: Band(title=None, steps=[
            _step(1, "Cross the road to the other side."), _step(2), _step(3),
        ])}

    unsafe_one = _template(template_id="fx_unsafe_1", title="Unsafe template", bands=_unsafe_bands())
    unsafe_two = _template(template_id="fx_unsafe_2", title="Unsafe template", bands=_unsafe_bands())

    class AlwaysUnsafeModelClient:
        def generate_text(self, prompt, max_tokens, timeout_s):
            return _rewrite_json({1: "Climb the tree over there.", 2: "Wave both arms.", 3: "Walk backwards."})

    missions = generate_missions(
        [unsafe_one, unsafe_two], PLACE_PLAYGROUND, fixtures.CLEAR_MILD, AgeBand.BAND_5_7, 20,
        model_client=AlwaysUnsafeModelClient(),
    )
    assert missions == []


#  B35: rejection-rate instrumentation


def test_stats_records_a_successful_generation_attempt():
    template = _template()
    client = FixtureModelClient(default_text=_rewrite_json({1: "a.", 2: "b.", 3: "c."}))
    stats = RejectionStats()

    generate_missions(
        [template], PLACE_PLAYGROUND, fixtures.CLEAR_MILD, AgeBand.BAND_5_7, 20,
        model_client=client, stats=stats,
    )
    assert stats.generation_attempts == 1
    assert stats.generation_rejections == 0


def test_stats_records_a_rejected_generation_by_constraint():
    unsafe = _template(title="Unsafe template")
    client = TitleAwareModelClient()
    stats = RejectionStats()

    generate_missions(
        [unsafe], PLACE_PLAYGROUND, fixtures.CLEAR_MILD, AgeBand.BAND_5_7, 20,
        model_client=client, stats=stats,
    )
    assert stats.generation_attempts == 1
    assert stats.generation_rejections == 1
    assert stats.by_constraint == {"no_climbing": 1}


def test_stats_do_not_count_pure_library_direct_calls():
    template = _template()
    stats = RejectionStats()

    generate_missions([template], PLACE_PLAYGROUND, fixtures.CLEAR_MILD, AgeBand.BAND_5_7, 20, stats=stats)
    assert stats.generation_attempts == 0


def test_stats_do_not_count_generation_that_fell_back_to_library_direct():
    template = _template()
    client = FixtureModelClient(default_text=None)  # generation fails, falls back
    stats = RejectionStats()

    generate_missions(
        [template], PLACE_PLAYGROUND, fixtures.CLEAR_MILD, AgeBand.BAND_5_7, 20,
        model_client=client, stats=stats,
    )
    assert stats.generation_attempts == 0


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
    # Two eligible candidates so exclusion has something to exclude
    # without B33/select_templates' own relaxation rule masking it.
    excluded = _template(template_id="fx_excluded", category="playground")
    other = _template(template_id="fx_other", category="any")

    missions = generate_missions(
        [excluded, other], PLACE_PLAYGROUND, fixtures.CLEAR_MILD, AgeBand.BAND_5_7, 20,
        preferences=["playground"],
    )
    assert [m.template_id for m in missions] == ["fx_other"]

    missions = generate_missions(
        [excluded, other], PLACE_PLAYGROUND, fixtures.CLEAR_MILD, AgeBand.BAND_5_7, 20,
        recent_template_ids=["fx_excluded"],
    )
    assert [m.template_id for m in missions] == ["fx_other"]
