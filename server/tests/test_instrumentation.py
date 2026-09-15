from __future__ import annotations

from app.missions.instrumentation import RejectionStats
from app.missions.models import ValidationResult


def test_passing_result_counts_as_an_attempt_with_no_rejection():
    stats = RejectionStats()
    stats.record(ValidationResult(ok=True), was_generated=True)
    assert stats.generation_attempts == 1
    assert stats.generation_rejections == 0
    assert stats.rejection_rate == 0.0


def test_library_direct_results_are_not_counted_at_all():
    stats = RejectionStats()
    stats.record(ValidationResult(ok=False, failures=["step 1: 'climb' violates no_climbing — rule"]), was_generated=False)
    assert stats.generation_attempts == 0
    assert stats.generation_rejections == 0
    assert stats.by_constraint == {}


def test_rejection_is_attributed_to_its_constraint():
    stats = RejectionStats()
    stats.record(
        ValidationResult(ok=False, failures=["step 1: 'climb' violates no_climbing — No step may ask a child to climb."]),
        was_generated=True,
    )
    assert stats.generation_attempts == 1
    assert stats.generation_rejections == 1
    assert stats.by_constraint == {"no_climbing": 1}


def test_multiple_failures_in_one_result_all_counted():
    stats = RejectionStats()
    stats.record(
        ValidationResult(ok=False, failures=[
            "step 1: 'climb' violates no_climbing — rule one",
            "step 2: 'cross the road' violates no_road_crossing — rule two",
        ]),
        was_generated=True,
    )
    assert stats.generation_rejections == 1  # one result, one rejection
    assert stats.by_constraint == {"no_climbing": 1, "no_road_crossing": 1}


def test_rejection_rate_across_several_records():
    stats = RejectionStats()
    stats.record(ValidationResult(ok=True), was_generated=True)
    stats.record(ValidationResult(ok=True), was_generated=True)
    stats.record(ValidationResult(ok=False, failures=["step 1: 'x' violates no_tasting — rule"]), was_generated=True)
    stats.record(ValidationResult(ok=False, failures=["step 1: 'x' violates no_tasting — rule"]), was_generated=True)

    assert stats.generation_attempts == 4
    assert stats.generation_rejections == 2
    assert stats.rejection_rate == 0.5
    assert stats.by_constraint == {"no_tasting": 2}


def test_rejection_rate_is_zero_with_no_attempts():
    assert RejectionStats().rejection_rate == 0.0


def test_non_matching_failure_string_is_not_attributed():
    stats = RejectionStats()
    stats.record(
        ValidationResult(ok=False, failures=["mission.template_id 'a' does not match template 'b'"]),
        was_generated=True,
    )
    assert stats.generation_rejections == 1
    assert stats.by_constraint == {}
