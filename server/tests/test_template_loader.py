from __future__ import annotations

from pathlib import Path

from app.missions.loader import DEFAULT_MISSIONS_DIR, load_template_dir, load_template_file
from app.missions.models import MissionTemplate
from app.models import AgeBand

CONTENT_MISSIONS_DIR = Path(__file__).resolve().parents[1] / "content" / "missions"


#  content/missions/reviewed/ — the real, review-approved library (default)


def test_default_directory_is_the_reviewed_library():
    assert DEFAULT_MISSIONS_DIR == CONTENT_MISSIONS_DIR / "reviewed"


def test_load_template_dir_with_no_args_loads_the_reviewed_library():
    families = load_template_dir()
    assert len(families) == 18
    assert all(isinstance(f, MissionTemplate) for f in families)


def test_reviewed_families_all_have_three_bands_and_seven_steps():
    # MIGRATION.md's own claim: "every family has three bands and seven steps."
    for family in load_template_dir():
        assert set(family.bands) == set(AgeBand)
        for band in family.bands.values():
            assert len(band.steps) == 7, family.template_id


def test_reviewed_families_use_category_any():
    # The real per-place-type data lives in mission_context_bindings.yaml
    # (eligible_place_categories), not on the template itself.
    for family in load_template_dir():
        assert family.category == "any"


def test_reviewed_families_are_all_reviewed_status():
    for family in load_template_dir():
        assert family.review.status.value == "reviewed", family.template_id


#  content/missions/*.yaml (top level) — older, superseded placeholder files.
#  Kept as-is (not deleted), so this just confirms the loader still parses
#  them correctly if pointed at that directory explicitly.


def test_every_legacy_mission_file_parses():
    families = load_template_dir(CONTENT_MISSIONS_DIR)
    assert families, "expected at least one template family under content/missions"
    assert all(isinstance(f, MissionTemplate) for f in families)


def test_candidates_subfolder_is_not_included():
    # _candidates/cycling_track_move_wet.yaml is a draft, not yet promoted to
    # the served library — load_template_dir is non-recursive, so its
    # template_ids must not leak into the main load.
    candidate_ids = {t.template_id for t in load_template_file(
        CONTENT_MISSIONS_DIR / "_candidates" / "cycling_track_move_wet.yaml"
    )}
    assert "speed_challenge" in candidate_ids

    loaded_ids = {f.template_id for f in load_template_dir(CONTENT_MISSIONS_DIR)}
    assert candidate_ids.isdisjoint(loaded_ids)


def test_playground_file_has_three_families():
    families = load_template_file(CONTENT_MISSIONS_DIR / "playground.yaml")
    assert len(families) == 3
    assert {f.duration_bucket for f in families} == {20, 40, 60}
