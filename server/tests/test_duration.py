from __future__ import annotations

import pytest

from app.models import DURATION_BUCKETS, DURATION_MIN_BOUNDS
from app.recommendation.duration import select_plan_bucket

LOW, HIGH = DURATION_MIN_BOUNDS


# The old tests pinned the 30/50 tie-break of nearest-bucket matching. The
# rule is now "largest bucket that fits the on-site budget", so the same
# boundaries are kept with new expectations. With no travel the budget is the
# total itself.
@pytest.mark.parametrize(
    ("total_min", "expected_bucket"),
    [
        (20, 20),
        (29, 20),
        (30, 20),
        (31, 20),
        (39, 20),
        (40, 40),
        (49, 40),
        (50, 40),
        (51, 40),
        (59, 40),
        (60, 60),
        (HIGH, 60),
    ],
)
def test_bucket_boundaries_without_travel(total_min: int, expected_bucket: int):
    assert select_plan_bucket(total_min, 0, 0) == expected_bucket


@pytest.mark.parametrize(
    ("total_min", "out_min", "back_min", "expected_bucket"),
    [
        (60, 10, 10, 40),  # 40 on site, exact fit
        (45, 7, 7, 20),  # 31 on site: 20, not 40
        (60, 5, 5, 40),  # 50 on site
        (70, 5, 5, 60),  # exactly 60 on site
        (69, 5, 5, 40),  # one minute short of 60
        (40, 10, 10, 20),  # exactly 20 on site
        (39, 10, 10, None),  # 19 on site, nothing fits
        (25, 10, 10, None),
        (120, 30, 30, 60),
        (20, 10, 10, None),  # all travel
        (20, 15, 15, None),  # travel exceeds the total
    ],
)
def test_bucket_after_travel(total_min, out_min, back_min, expected_bucket):
    assert select_plan_bucket(total_min, out_min, back_min) == expected_bucket


def test_out_and_back_are_summed_not_assumed_equal():
    assert select_plan_bucket(60, 5, 15) == 40
    assert select_plan_bucket(60, 15, 5) == 40
    assert select_plan_bucket(60, 20, 0) == 40


@pytest.mark.parametrize("invalid_total", [LOW - 1, HIGH + 1, 0, -20, 500])
def test_out_of_range_total_rejected(invalid_total: int):
    with pytest.raises(ValueError):
        select_plan_bucket(invalid_total, 0, 0)


@pytest.mark.parametrize(
    "bad", [(60, -1, 5), (60, 5, -1), (60.0, 5, 5), (60, True, 5), (60, "5", 5)]
)
def test_invalid_inputs_rejected(bad):
    with pytest.raises(ValueError):
        select_plan_bucket(*bad)


def test_rule_holds_across_full_range():
    previous = 0
    for total in range(LOW, HIGH + 1):
        chosen = select_plan_bucket(total, 0, 0)
        assert chosen in DURATION_BUCKETS
        assert chosen <= total
        assert chosen >= previous
        # largest bucket that fits: no bigger bucket also fits
        assert all(b <= chosen for b in DURATION_BUCKETS if b <= total)
        previous = chosen


def test_more_travel_never_lengthens_the_plan():
    for total in range(LOW, HIGH + 1):
        last = max(DURATION_BUCKETS)
        for trip in range(0, 61):
            bucket = select_plan_bucket(total, trip, trip)
            assert bucket is None or bucket <= last
            last = bucket if bucket is not None else 0
