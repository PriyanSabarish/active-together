"""Story 9.2 — the parent guide content for the at-home activities."""

from app.missions import guides
from app.missions.service import HOME_TEMPLATES


def test_every_home_template_has_a_guide_and_only_those():
    assert guides.guided_template_ids() == {t.template_id for t in HOME_TEMPLATES}


def test_a_guide_covers_every_stage_the_missions_can_reach():
    for t in HOME_TEMPLATES:
        guide = guides.guide_for(t.template_id)
        steps_at_40 = 5
        assert len(guide["stages"]) == steps_at_40
        assert guide["setupTime"].endswith("min")
        assert guide["rules"]


def test_each_stage_has_a_note_for_every_age_band_where_it_has_any():
    for t in HOME_TEMPLATES:
        for stage in guides.guide_for(t.template_id)["stages"]:
            for part in stage["parts"]:
                if part.get("bands"):
                    assert set(part["bands"]) == set(guides.AGE_BANDS), (t.template_id, stage["title"])


def test_outdoor_templates_have_no_guide():
    assert guides.guide_for("activity_colour_hunt") is None


def test_the_safety_rules_forbid_climbing_furniture_and_throwing_at_people():
    text = " ".join(guides.guide_for("activity_home_sock_ball_carnival")["rules"]).lower()
    assert "do not climb" in text and "never at faces or bodies" in text
