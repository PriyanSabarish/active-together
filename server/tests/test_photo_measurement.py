"""Measurement and vocabulary writing (B54)."""

from __future__ import annotations

import shutil

import pytest
import yaml

from app.photo.measurement import (
    MIN_PER_SET,
    fit_threshold,
    measure_checker,
    measure_scores,
    overall_status,
    update_vocabulary,
    wilson_interval,
)
from app.photo.models import Prompt, ScorerStatus
from app.photo.scorers import API, OWN_HOST, FixtureImageScorer
from app.photo.vocabulary import VOCABULARY_PATH, load_vocabulary

PROMPT = Prompt("p_green", "something green")


def test_wilson_interval_known_values():
    low, high = wilson_interval(8, 10)
    assert low == pytest.approx(0.490, abs=0.005)
    assert high == pytest.approx(0.943, abs=0.005)
    assert wilson_interval(0, 0) == (0.0, 1.0)
    low, high = wilson_interval(10, 10)
    assert high == 1.0 and low == pytest.approx(0.722, abs=0.005)


def test_small_samples_get_wide_intervals():
    small = wilson_interval(5, 5)
    large = wilson_interval(50, 50)
    assert (1 - small[0]) > (1 - large[0])


def test_fit_threshold_separates_clean_scores():
    t, correct = fit_threshold([0.4, 0.5, 0.6], [0.1, 0.2, 0.3])
    assert correct == 6
    assert 0.3 < t <= 0.4


def test_fit_threshold_ties_choose_the_stricter_value():
    # every threshold between 0.3 and 0.4 is equally good; observed scores only
    t, _ = fit_threshold([0.4], [0.3])
    assert t == 0.4


def test_fit_threshold_on_overlapping_scores():
    t, correct = fit_threshold([0.2, 0.5, 0.6], [0.1, 0.3, 0.55])
    assert correct == sum(s >= t for s in [0.2, 0.5, 0.6]) + sum(s < t for s in [0.1, 0.3, 0.55])


def photos(n):
    return [f"p{i}".encode() for i in range(n)]


def test_checker_measurement_keeps_a_strong_prompt():
    pos, neg = photos(40), [f"n{i}".encode() for i in range(40)]

    class Oracle(FixtureImageScorer):
        def check(self, image_bytes, prompt):
            return image_bytes.startswith(b"p")

    m = measure_checker(Oracle(API), PROMPT, pos, neg)
    assert (m.true_positive, m.true_negative, m.positives, m.negatives) == (40, 40, 40, 40)
    assert m.status.status == "kept"
    assert m.status.accuracy == 1.0
    assert m.status.ci_low > 0.9
    assert m.status.threshold is None


def test_near_misses_that_fool_the_scorer_drop_the_prompt():
    pos = photos(20)
    neg = [f"n{i}".encode() for i in range(20)]
    # says yes to everything: perfect on positives, wrong on every near-miss
    m = measure_checker(FixtureImageScorer(API, default=True), PROMPT, pos, neg)
    assert m.true_negative == 0
    assert m.status.accuracy == 0.5
    assert m.status.status == "dropped"


def test_too_few_photos_drops_the_prompt_even_when_perfect():
    n = MIN_PER_SET - 1
    m = measure_checker(
        FixtureImageScorer(API, default=True), PROMPT, photos(n), []
    )
    assert m.status.status == "dropped"


def test_unanswered_photos_count_as_wrong_and_are_reported():
    m = measure_checker(FixtureImageScorer(API, fail=True), PROMPT, photos(15), photos(15))
    assert m.skipped == 30
    assert m.status.accuracy == 0.0
    assert m.status.status == "dropped"


def test_scores_measurement_fits_and_keeps_a_threshold():
    scores = {f"p{i}".encode(): 0.4 + i * 0.001 for i in range(30)}
    scores.update({f"n{i}".encode(): 0.1 + i * 0.001 for i in range(30)})
    m = measure_scores(
        PROMPT, OWN_HOST, lambda photo, text: scores[photo],
        [f"p{i}".encode() for i in range(30)], [f"n{i}".encode() for i in range(30)],
    )
    assert m.status.status == "kept"
    assert 0.13 < m.status.threshold <= 0.4
    assert m.status.accuracy == 1.0


def test_overlapping_scores_are_dropped_not_given_a_lower_threshold():
    pos = [f"p{i}".encode() for i in range(30)]
    neg = [f"n{i}".encode() for i in range(30)]
    scores = {p: 0.2 + (i % 5) * 0.01 for i, p in enumerate(pos)}
    scores.update({n: 0.2 + (i % 5) * 0.01 for i, n in enumerate(neg)})
    m = measure_scores(PROMPT, OWN_HOST, lambda photo, text: scores[photo], pos, neg)
    assert m.status.status == "dropped"
    assert m.status.threshold is None


def test_empty_sets_do_not_crash():
    m = measure_scores(PROMPT, OWN_HOST, lambda *_: 0.0, [], [])
    assert m.status.status == "dropped"


# vocabulary.yaml writing


def test_overall_status_rule():
    assert overall_status({}) == "candidate"
    assert overall_status({"api": {"status": "kept"}}) == "kept"
    assert overall_status({"api": {"status": "dropped"}}) == "candidate"  # clip not measured yet
    assert overall_status({"api": {"status": "dropped"}, "own_host": {"status": "dropped"}}) == "dropped"
    assert overall_status({"api": {"status": "dropped"}, "own_host": {"status": "kept"}}) == "kept"


@pytest.fixture
def vocab_copy(tmp_path):
    path = tmp_path / "vocabulary.yaml"
    shutil.copy(VOCABULARY_PATH, path)
    return path


def test_update_changes_only_the_named_prompt_and_keeps_comments(vocab_copy):
    before = vocab_copy.read_text(encoding="utf-8").splitlines()
    changed = update_vocabulary(
        vocab_copy, {"p_red": {API: ScorerStatus("kept", accuracy=0.95, ci_low=0.84, ci_high=0.98)}}
    )
    after = vocab_copy.read_text(encoding="utf-8").splitlines()
    assert changed == 1
    assert len(after) == len(before)
    diff = [i for i, (a, b) in enumerate(zip(before, after)) if a != b]
    assert len(diff) == 1
    assert any(line.startswith("#") for line in after)
    assert "excluded_by_design:" in after


def test_updated_file_still_loads_and_passes_the_mission_checks_shape(vocab_copy):
    update_vocabulary(
        vocab_copy,
        {
            "p_red": {API: ScorerStatus("kept", accuracy=0.95, ci_low=0.84, ci_high=0.98)},
            "p_leaf": {OWN_HOST: ScorerStatus("kept", threshold=0.27, accuracy=0.9, ci_low=0.8, ci_high=0.95)},
            "p_green": {API: ScorerStatus("dropped", accuracy=0.6, ci_low=0.4, ci_high=0.7)},
        },
    )
    raw = yaml.safe_load(vocab_copy.read_text(encoding="utf-8"))
    by_id = {p["id"]: p for p in raw["prompts"]}
    # the checks in content/tools/mission_checks.py read id, text and top-level status
    assert all(p["status"] in ("candidate", "kept", "dropped") for p in raw["prompts"])
    assert by_id["p_red"]["status"] == "kept"
    assert by_id["p_leaf"]["status"] == "kept"
    assert by_id["p_green"]["status"] == "candidate"
    prompts = load_vocabulary(vocab_copy)
    assert prompts["p_red"].kept_for(API) and not prompts["p_red"].kept_for(OWN_HOST)
    assert prompts["p_leaf"].scorers[OWN_HOST].threshold == 0.27
    assert not prompts["p_green"].kept_for(API)
    assert prompts["p_red"].text == "something red"


def test_second_measurement_merges_with_the_first(vocab_copy):
    update_vocabulary(vocab_copy, {"p_red": {API: ScorerStatus("kept", accuracy=0.9)}})
    update_vocabulary(vocab_copy, {"p_red": {OWN_HOST: ScorerStatus("dropped", accuracy=0.5)}})
    prompt = load_vocabulary(vocab_copy)["p_red"]
    assert prompt.kept_for(API)
    assert prompt.scorers[OWN_HOST].status == "dropped"


def test_unknown_prompt_ids_are_ignored(vocab_copy):
    before = vocab_copy.read_text(encoding="utf-8")
    assert update_vocabulary(vocab_copy, {"p_nope": {API: ScorerStatus("kept")}}) == 0
    assert vocab_copy.read_text(encoding="utf-8") == before
