"""verify_step() and the scorer chain (B51, B55), plan section 7 scenarios."""

from __future__ import annotations

import pytest

from app.photo.models import Prompt, ScorerStatus, Verification
from app.photo.scorers import API, OWN_HOST, FixtureImageScorer, ImageScorer
from app.photo.verify import verify_step
from app.photo.vocabulary import load_vocabulary

IMAGE = b"\xff\xd8fake-jpeg"


def vocab(**kept_for: tuple[str, ...]) -> dict[str, Prompt]:
    """vocab(p_red=("api",), p_leaf=("api", "own_host")) -> kept per scorer."""
    return {
        pid: Prompt(
            pid,
            f"text for {pid}",
            {name: ScorerStatus("kept", threshold=0.3 if name == OWN_HOST else None) for name in names},
        )
        for pid, names in kept_for.items()
    }


def api(**kw) -> FixtureImageScorer:
    return FixtureImageScorer(API, **kw)


def host(**kw) -> FixtureImageScorer:
    return FixtureImageScorer(OWN_HOST, **kw)


def test_fixture_scorer_satisfies_the_interface():
    assert isinstance(api(), ImageScorer)


def test_host_not_deployed_is_checked_by_the_api():
    v = verify_step(IMAGE, "p_red", 1, [host(is_available=False), api()], vocab(p_red=(API, OWN_HOST)))
    assert v == Verification("confirmed", 2, "api")


def test_hosted_scorer_goes_first_when_available():
    h, a = host(), api()
    v = verify_step(IMAGE, "p_red", 1, [h, a], vocab(p_red=(API, OWN_HOST)))
    assert v.checked_by == "own_host"
    assert a.calls == []


@pytest.mark.parametrize(("attempt", "left"), [(1, 2), (2, 1), (3, 0)])
def test_confirmed_reports_attempts_left(attempt, left):
    v = verify_step(IMAGE, "p_red", attempt, [api()], vocab(p_red=(API,)))
    assert v == Verification("confirmed", left, "api")


def test_ambiguous_photo_gives_retry_retry_then_use_tap():
    scorers = [api(default=False)]
    v = vocab(p_red=(API,))
    assert verify_step(IMAGE, "p_red", 1, scorers, v) == Verification("retry", 2, "api")
    assert verify_step(IMAGE, "p_red", 2, scorers, v) == Verification("retry", 1, "api")
    assert verify_step(IMAGE, "p_red", 3, scorers, v) == Verification("use_tap", 0, "api")


def test_a_late_match_still_confirms():
    flip = api(answers={"p_red": True})
    assert verify_step(IMAGE, "p_red", 3, [flip], vocab(p_red=(API,))).result == "confirmed"


def test_host_and_api_both_unreachable_gives_use_tap_on_the_first_attempt():
    v = verify_step(
        IMAGE, "p_red", 1, [host(fail=True), api(fail=True)], vocab(p_red=(API, OWN_HOST))
    )
    assert v == Verification("use_tap", 0, None)


def test_scorers_not_available_gives_use_tap_at_once():
    v = verify_step(
        IMAGE, "p_red", 1, [host(is_available=False), api(is_available=False)], vocab(p_red=(API, OWN_HOST))
    )
    assert v == Verification("use_tap", 0, None)


def test_no_scorers_at_all_gives_use_tap():
    assert verify_step(IMAGE, "p_red", 2, [], vocab(p_red=(API,))) == Verification("use_tap", 0, None)


def test_scorer_that_errors_falls_through_to_the_next():
    v = verify_step(IMAGE, "p_red", 1, [host(fail=True), api()], vocab(p_red=(API, OWN_HOST)))
    assert v == Verification("confirmed", 2, "api")


def test_prompt_kept_for_clip_only_and_host_down_gives_use_tap_without_calling_the_api():
    a = api()
    v = verify_step(IMAGE, "p_red", 1, [host(is_available=False), a], vocab(p_red=(OWN_HOST,)))
    assert v == Verification("use_tap", 0, None)
    assert a.calls == []


def test_prompt_kept_for_api_only_skips_the_host():
    h = host()
    v = verify_step(IMAGE, "p_red", 1, [h, api()], vocab(p_red=(API,)))
    assert v.checked_by == "api"
    assert h.calls == []


def test_candidate_and_dropped_prompts_are_never_scored():
    a = api()
    prompts = {
        "p_c": Prompt("p_c", "c", {API: ScorerStatus("candidate")}),
        "p_d": Prompt("p_d", "d", {API: ScorerStatus("dropped")}),
        "p_n": Prompt("p_n", "n"),
    }
    for pid in prompts:
        assert verify_step(IMAGE, pid, 1, [a], prompts).result == "use_tap"
    assert a.calls == []


def test_unknown_prompt_id_gives_use_tap():
    assert verify_step(IMAGE, "p_nope", 1, [api()], vocab(p_red=(API,))) == Verification("use_tap", 0, None)


@pytest.mark.parametrize("attempt", [0, 4, -1, 1.5, "1", True])
def test_invalid_attempt_rejected(attempt):
    with pytest.raises(ValueError):
        verify_step(IMAGE, "p_red", attempt, [api()], vocab(p_red=(API,)))


def test_result_shape_matches_the_contract():
    v = verify_step(IMAGE, "p_red", 1, [api()], vocab(p_red=(API,)))
    assert set(vars(v)) == {"result", "attempts_left", "checked_by"}
    assert v.result in {"confirmed", "retry", "use_tap"}
    assert v.checked_by in {"own_host", "api", None}


def test_real_vocabulary_has_nothing_kept_until_it_is_measured():
    """Every shipped prompt is a candidate, so the default chain taps."""
    prompts = load_vocabulary()
    assert len(prompts) == 20
    assert not any(p.kept_for(API) or p.kept_for(OWN_HOST) for p in prompts.values())
    assert verify_step(IMAGE, "p_red", 1, [api(), host()], prompts).result == "use_tap"


# PHOTO_REQUIRE_MEASURED=false: the gate is off, not removed


def candidate_vocab() -> dict[str, Prompt]:
    return {
        "p_new": Prompt("p_new", "new"),
        "p_cand": Prompt("p_cand", "cand", {API: ScorerStatus("candidate")}),
        "p_drop": Prompt("p_drop", "drop", {API: ScorerStatus("dropped")}),
    }


def test_gate_on_by_default_blocks_candidates():
    a = api()
    assert verify_step(IMAGE, "p_new", 1, [a], candidate_vocab(), require_measured=True).result == "use_tap"
    assert a.calls == []


def test_gate_off_asks_the_api_about_candidate_prompts():
    for pid in ("p_new", "p_cand"):
        v = verify_step(IMAGE, pid, 1, [api()], candidate_vocab(), require_measured=False)
        assert v == Verification("confirmed", 2, "api")


def test_gate_off_still_never_asks_about_dropped_prompts():
    a = api()
    v = verify_step(IMAGE, "p_drop", 1, [a], candidate_vocab(), require_measured=False)
    assert v == Verification("use_tap", 0, None)
    assert a.calls == []


def test_gate_off_keeps_the_retry_rule():
    scorers = [api(default=False)]
    results = [verify_step(IMAGE, "p_new", n, scorers, candidate_vocab(), require_measured=False).result for n in (1, 2, 3)]
    assert results == ["retry", "retry", "use_tap"]


def test_gate_off_with_the_api_down_still_taps():
    v = verify_step(IMAGE, "p_new", 1, [api(fail=True)], candidate_vocab(), require_measured=False)
    assert v == Verification("use_tap", 0, None)


def test_flag_is_read_from_settings(monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "photo_require_measured", False)
    assert verify_step(IMAGE, "p_new", 1, [api()], candidate_vocab()).result == "confirmed"
    monkeypatch.setattr(settings, "photo_require_measured", True)
    assert verify_step(IMAGE, "p_new", 1, [api()], candidate_vocab()).result == "use_tap"
