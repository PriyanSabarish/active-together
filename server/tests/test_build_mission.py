from __future__ import annotations

import pytest

from app.missions.builder import build_mission
from app.missions.models import Band, MissionTemplate, Review, TemplateStep
from app.models import AgeBand
from tests import mission_fixtures as fx


def test_truncates_to_three_for_20_minutes():
    mission = build_mission(fx.MULTI_BAND_FAMILY, AgeBand.BAND_11_12, 20)
    assert [s.sequence for s in mission.steps] == [1, 2, 3]
    assert mission.estimated_minutes == 20


def test_truncates_to_five_for_40_minutes():
    mission = build_mission(fx.MULTI_BAND_FAMILY, AgeBand.BAND_8_10, 40)
    assert [s.sequence for s in mission.steps] == [1, 2, 3, 4, 5]
    assert mission.estimated_minutes == 40


def test_keeps_all_seven_for_60_minutes():
    mission = build_mission(fx.MULTI_BAND_FAMILY, AgeBand.BAND_5_7, 60)
    assert [s.sequence for s in mission.steps] == [1, 2, 3, 4, 5, 6, 7]
    assert mission.estimated_minutes == 60


def test_exact_fit_band_returns_all_its_steps():
    mission = build_mission(fx.BUCKET20_BAND_5_7_SELF, AgeBand.BAND_5_7, 20)
    assert len(mission.steps) == 3


def test_requesting_more_steps_than_authored_raises():
    with pytest.raises(ValueError, match="has only 3 steps, needs 7"):
        build_mission(fx.BUCKET20_BAND_5_7_SELF, AgeBand.BAND_5_7, 60)


def test_requesting_missing_band_raises():
    with pytest.raises(ValueError, match="has no '11-12' band"):
        build_mission(fx.BUCKET20_BAND_5_7_SELF, AgeBand.BAND_11_12, 20)


def test_invalid_duration_bucket_raises():
    with pytest.raises(ValueError, match="duration_bucket must be one of"):
        build_mission(fx.MULTI_BAND_FAMILY, AgeBand.BAND_5_7, 30)


def test_equipment_passes_through():
    mission = build_mission(fx.WITH_EQUIPMENT, AgeBand.BAND_8_10, 40)
    assert mission.equipment == ["bicycle", "helmet"]


def test_verify_mode_and_prompt_id_pass_through_unchanged():
    mission = build_mission(fx.BUCKET20_BAND_5_7_PHOTO, AgeBand.BAND_5_7, 20)
    modes = [(s.verify_mode.value, s.prompt_id) for s in mission.steps]
    assert modes == [("photo", "p_green"), ("photo", "p_red"), ("self", None)]


def test_two_calls_produce_different_mission_ids():
    first = build_mission(fx.MULTI_BAND_FAMILY, AgeBand.BAND_5_7, 20)
    second = build_mission(fx.MULTI_BAND_FAMILY, AgeBand.BAND_5_7, 20)
    assert first.mission_id != second.mission_id


def test_band_title_overrides_family_title():
    template = MissionTemplate(
        template_id="fx_title_override",
        title="Family title",
        category="playground",
        duration_bucket=20,
        weather_tags=["any"],
        site_requirements=["grass"],
        equipment=[],
        mechanic="move",
        bands={
            AgeBand.BAND_5_7: Band(
                title="Band-specific title",
                steps=[
                    TemplateStep(sequence=1, prompt_text="Step one.", verify_mode="self", prompt_id=None, variable=True),
                    TemplateStep(sequence=2, prompt_text="Step two.", verify_mode="self", prompt_id=None, variable=True),
                    TemplateStep(sequence=3, prompt_text="Step three.", verify_mode="self", prompt_id=None, variable=True),
                ],
            )
        },
        safety_tags=["inherited"],
        review=Review(author="fixture", reviewed_by=None, status="draft"),
    )

    mission = build_mission(template, AgeBand.BAND_5_7, 20)
    assert mission.title == "Band-specific title"


def test_steps_are_sorted_by_sequence_even_if_authored_out_of_order():
    template = MissionTemplate(
        template_id="fx_out_of_order",
        title="Out of order",
        category="playground",
        duration_bucket=20,
        weather_tags=["any"],
        site_requirements=["grass"],
        equipment=[],
        mechanic="move",
        bands={
            AgeBand.BAND_5_7: Band(
                title=None,
                steps=[
                    TemplateStep(sequence=3, prompt_text="Third.", verify_mode="self", prompt_id=None, variable=True),
                    TemplateStep(sequence=1, prompt_text="First.", verify_mode="self", prompt_id=None, variable=True),
                    TemplateStep(sequence=2, prompt_text="Second.", verify_mode="self", prompt_id=None, variable=True),
                ],
            )
        },
        safety_tags=["inherited"],
        review=Review(author="fixture", reviewed_by=None, status="draft"),
    )

    mission = build_mission(template, AgeBand.BAND_5_7, 20)
    assert [s.prompt_text for s in mission.steps] == ["First.", "Second.", "Third."]
