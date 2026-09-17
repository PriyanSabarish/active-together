from __future__ import annotations

from app.missions.models import Band, MissionTemplate, Review, TemplateStep
from app.missions.schema_validator import validate_schema
from app.models import AgeBand
from tests import mission_fixtures as fx


def _step(sequence: int, words: int = 3, **overrides):
    text = " ".join(["word"] * words) + "."
    defaults = dict(prompt_text=text, verify_mode="self", prompt_id=None, variable=True)
    return TemplateStep(sequence=sequence, **{**defaults, **overrides})


def _template(**overrides):
    defaults = dict(
        template_id="fx_schema_test",
        title="Schema test",
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


def test_exact_fit_template_passes():
    result = validate_schema(_template())
    assert result.ok
    assert result.failures == []


def test_real_content_fixtures_pass():
    for template in fx.TEMPLATES:
        result = validate_schema(template)
        assert result.ok, f"{template.template_id} failed: {result.failures}"


def test_too_few_steps_for_bucket_fails():
    template = _template(duration_bucket=40, bands={
        AgeBand.BAND_8_10: Band(title=None, steps=[_step(1), _step(2), _step(3)])
    })
    result = validate_schema(template)
    assert not result.ok
    assert any("has 3 steps, expected 5" in f for f in result.failures)


def test_too_many_steps_for_bucket_fails():
    template = _template(duration_bucket=20, bands={
        AgeBand.BAND_5_7: Band(title=None, steps=[_step(i) for i in range(1, 6)])
    })
    result = validate_schema(template)
    assert not result.ok
    assert any("has 5 steps, expected 3" in f for f in result.failures)


def test_inconsistent_band_step_counts_fails():
    template = _template(duration_bucket=60, bands={
        AgeBand.BAND_5_7: Band(title=None, steps=[_step(i) for i in range(1, 8)]),
        AgeBand.BAND_8_10: Band(title=None, steps=[_step(i) for i in range(1, 7)]),
    })
    result = validate_schema(template)
    assert not result.ok
    assert any("do not all have the same step count" in f for f in result.failures)
    # the 8-10 band with 6 steps also independently violates the exact-count rule
    assert any("band '8-10' has 6 steps" in f for f in result.failures)


def test_multi_band_family_with_equal_counts_passes():
    result = validate_schema(fx.MULTI_BAND_FAMILY)
    assert result.ok


def test_5_7_band_over_word_limit_fails():
    template = _template(bands={
        AgeBand.BAND_5_7: Band(title=None, steps=[_step(1, words=13), _step(2), _step(3)])
    })
    result = validate_schema(template)
    assert not result.ok
    assert any("has 13 words (max 12)" in f for f in result.failures)


def test_5_7_band_at_word_limit_passes():
    template = _template(bands={
        AgeBand.BAND_5_7: Band(title=None, steps=[_step(1, words=12), _step(2), _step(3)])
    })
    result = validate_schema(template)
    assert result.ok


def test_word_limit_does_not_apply_to_older_bands():
    template = _template(duration_bucket=20, bands={
        AgeBand.BAND_11_12: Band(title=None, steps=[_step(1, words=20), _step(2), _step(3)])
    })
    result = validate_schema(template)
    assert result.ok
