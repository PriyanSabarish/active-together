from __future__ import annotations

from app.models import AgeBand, VerifyMode
from tests import mission_fixtures as fx


def _all_template_bands():
    for template in fx.TEMPLATES:
        yield from template.bands.keys()


def _all_template_verify_modes():
    for template in fx.TEMPLATES:
        for band in template.bands.values():
            for step in band.steps:
                yield step.verify_mode


def _all_mission_verify_modes():
    for mission in fx.MISSIONS:
        for step in mission.steps:
            yield step.verify_mode


def test_templates_cover_every_age_band():
    assert set(_all_template_bands()) == set(AgeBand)


def test_templates_cover_every_duration_bucket():
    assert {t.duration_bucket for t in fx.TEMPLATES} == {20, 40, 60}


def test_templates_cover_both_verify_modes():
    assert set(_all_template_verify_modes()) == set(VerifyMode)


def test_missions_cover_every_age_band():
    assert {m.age_band for m in fx.MISSIONS} == set(AgeBand)


def test_missions_cover_every_bucket_via_estimated_minutes():
    assert {m.estimated_minutes for m in fx.MISSIONS} == {20, 40, 60}


def test_missions_cover_both_verify_modes():
    assert set(_all_mission_verify_modes()) == set(VerifyMode)


def test_bare_site_category_is_covered():
    assert any(t.category == "any" for t in fx.TEMPLATES)


def test_non_empty_equipment_is_covered():
    assert any(t.equipment for t in fx.TEMPLATES)
    assert any(m.equipment for m in fx.MISSIONS)


def test_multi_band_family_has_all_three_bands():
    assert set(fx.MULTI_BAND_FAMILY.bands.keys()) == set(AgeBand)


def test_multi_band_family_bands_hold_seven_steps_for_truncation():
    for band in fx.MULTI_BAND_FAMILY.bands.values():
        assert len(band.steps) == 7
