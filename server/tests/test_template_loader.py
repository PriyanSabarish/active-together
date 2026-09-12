from __future__ import annotations

from pathlib import Path

from app.missions.loader import load_template_dir, load_template_file
from app.missions.models import MissionTemplate

CONTENT_MISSIONS_DIR = Path(__file__).resolve().parents[2] / "content" / "missions"


def test_every_reviewed_mission_file_parses():
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
