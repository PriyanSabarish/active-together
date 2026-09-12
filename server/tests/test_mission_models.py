from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.missions.models import Band, MissionTemplate, Review, TemplateStep


def _step(**overrides):
    defaults = dict(sequence=1, prompt_text="Hop to the fence.", verify_mode="self", variable=True)
    return TemplateStep(**{**defaults, **overrides})


def _template(**overrides):
    defaults = dict(
        template_id="play_animal_moves",
        title="Animal moves",
        category="playground",
        duration_bucket=20,
        weather_tags=["any"],
        site_requirements=["grass"],
        equipment=[],
        mechanic="move",
        bands={"5-7": Band(title=None, steps=[_step()])},
        safety_tags=["inherited"],
        review=Review(author="bulk-draft", reviewed_by=None, status="draft"),
    )
    return MissionTemplate(**{**defaults, **overrides})


def test_minimal_template_parses():
    template = _template()
    assert template.template_id == "play_animal_moves"
    assert template.bands["5-7"].steps[0].prompt_text == "Hop to the fence."


def test_photo_step_requires_prompt_id():
    with pytest.raises(ValidationError, match="prompt_id is required"):
        _step(verify_mode="photo", prompt_id=None)


def test_photo_step_with_prompt_id_is_valid():
    step = _step(verify_mode="photo", prompt_id="p_fence")
    assert step.prompt_id == "p_fence"


def test_self_step_does_not_require_prompt_id():
    step = _step(verify_mode="self")
    assert step.prompt_id is None


def test_invalid_duration_bucket_rejected():
    with pytest.raises(ValidationError, match="duration_bucket must be one of"):
        _template(duration_bucket=30)


def test_template_requires_at_least_one_band():
    with pytest.raises(ValidationError):
        _template(bands={})


def test_unknown_verify_mode_rejected():
    with pytest.raises(ValidationError):
        _step(verify_mode="video")


def test_unknown_mechanic_rejected():
    with pytest.raises(ValidationError):
        _template(mechanic="dance")


def test_equipment_defaults_to_empty_list():
    template = _template()
    template_data = template.model_dump()
    del template_data["equipment"]
    rebuilt = MissionTemplate(**template_data)
    assert rebuilt.equipment == []
