from __future__ import annotations

import pytest

from app.models import DURATION_BUCKETS, DURATION_MIN_BOUNDS
from app.recommendation.duration import match_bucket

LOW, HIGH = DURATION_MIN_BOUNDS


@pytest.mark.parametrize(
    ("duration_min", "expected_bucket"),
    [
        (29, 20),
        (30, 20),
        (31, 40),
        (49, 40),
        (50, 40),
        (51, 60),
    ],
)
def test_match_bucket_tie_boundaries(duration_min: int, expected_bucket: int):
    assert match_bucket(duration_min) == expected_bucket


@pytest.mark.parametrize("invalid_duration", [LOW - 1, HIGH + 1, 0, -20, 500])
def test_out_of_range_rejected(invalid_duration: int):
    with pytest.raises(ValueError):
        match_bucket(invalid_duration)


def test_rule_holds_across_full_range():
    previous = 0
    for duration in range(LOW, HIGH + 1):
        chosen = match_bucket(duration)
        diff = abs(duration - chosen)

        assert chosen in DURATION_BUCKETS
        assert chosen >= previous
        assert all(diff <= abs(duration - b) for b in DURATION_BUCKETS)

        tied = [b for b in DURATION_BUCKETS if abs(duration - b) == diff]
        assert chosen == min(tied)

        previous = chosen