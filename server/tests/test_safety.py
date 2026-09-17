from __future__ import annotations

from app.missions.safety import SafetyConstraint, validate_mission
from app.models import AgeBand, Mission, Step, VerifyMode
from tests import mission_fixtures as fx

TEMPLATE = fx.BUCKET20_BAND_5_7_SELF


def _mission(steps: list[Step], template_id: str = TEMPLATE.template_id) -> Mission:
    return Mission(
        mission_id="fxm_safety_test",
        template_id=template_id,
        title="Safety test",
        age_band=AgeBand.BAND_5_7,
        estimated_minutes=20,
        equipment=[],
        steps=steps,
    )


def _step(sequence: int, prompt_text: str) -> Step:
    return Step(sequence=sequence, prompt_text=prompt_text, verify_mode=VerifyMode.SELF, prompt_id=None)


def test_benign_mission_passes():
    mission = _mission([_step(1, "Hop to the fence."), _step(2, "Wave both arms.")])
    result = validate_mission(mission, TEMPLATE)
    assert result.ok
    assert result.failures == []


def test_climb_the_tree_is_rejected():
    mission = _mission([_step(1, "Climb the tree over there.")])
    result = validate_mission(mission, TEMPLATE)
    assert not result.ok
    assert any("no_climbing" in f for f in result.failures)


def test_cross_the_road_is_rejected():
    mission = _mission([_step(1, "Cross the road to the other side.")])
    result = validate_mission(mission, TEMPLATE)
    assert not result.ok
    assert any("no_road_crossing" in f for f in result.failures)


def test_out_of_sight_is_rejected():
    mission = _mission([_step(1, "Run ahead and go out of sight of the bench.")])
    result = validate_mission(mission, TEMPLATE)
    assert not result.ok
    assert any("stay_in_sight" in f for f in result.failures)


def test_matching_is_case_insensitive():
    mission = _mission([_step(1, "CLIMB the play structure.")])
    result = validate_mission(mission, TEMPLATE)
    assert not result.ok


def test_mismatched_template_id_is_a_failure():
    mission = _mission([_step(1, "Hop to the fence.")], template_id="some_other_template")
    result = validate_mission(mission, TEMPLATE)
    assert not result.ok
    assert any("does not match" in f for f in result.failures)


def test_one_step_can_trigger_multiple_constraints():
    mission = _mission([_step(1, "Climb the fence then cross the road.")])
    result = validate_mission(mission, TEMPLATE)
    assert not result.ok
    assert any("no_climbing" in f for f in result.failures)
    assert any("no_road_crossing" in f for f in result.failures)


def test_all_fixture_missions_pass_the_real_constraints():
    for mission in fx.MISSIONS:
        result = validate_mission(mission, TEMPLATE)
        # template_id mismatch is expected noise here since these missions
        # belong to different templates — check only for safety failures.
        safety_failures = [f for f in result.failures if "does not match" not in f]
        assert not safety_failures, f"{mission.mission_id} failed: {safety_failures}"


def test_custom_constraints_override_the_real_file():
    custom = (SafetyConstraint(id="no_purple", rule="No step may mention purple.", rejects=["purple"]),)
    mission = _mission([_step(1, "Find something purple.")])
    result = validate_mission(mission, TEMPLATE, constraints=custom)
    assert not result.ok
    assert any("no_purple" in f for f in result.failures)

    # and the real "climb" phrase no longer triggers anything with this override
    climbing_mission = _mission([_step(1, "Climb the tree.")])
    result_climb = validate_mission(climbing_mission, TEMPLATE, constraints=custom)
    assert result_climb.ok
