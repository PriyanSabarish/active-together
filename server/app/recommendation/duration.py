from __future__ import annotations

from app.models import DURATION_BUCKETS, DURATION_MIN_BOUNDS


def _require_int(name: str, value: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{name} must be an integer, got {value!r} ({type(value).__name__})")


def select_plan_bucket(total_min: int, out_min: int, back_min: int) -> int | None:
    """
    Largest plan bucket (20, 40 or 60) that fits the on-site budget, else None.

    The on-site budget is the parent's total time minus travel out and back.
    A bucket fits when it is <= the budget, so an exact fit counts: 60 total
    with 10 minutes each way leaves 40, which takes the 40 minute plan.
    """
    low, high = DURATION_MIN_BOUNDS
    _require_int("total_min", total_min)
    _require_int("out_min", out_min)
    _require_int("back_min", back_min)
    if not (low <= total_min <= high):
        raise ValueError(f"Total time must be between {low} and {high} minutes, got {total_min}")
    if out_min < 0 or back_min < 0:
        raise ValueError(f"Travel times cannot be negative, got out={out_min}, back={back_min}")

    on_site = total_min - out_min - back_min
    fitting = [bucket for bucket in DURATION_BUCKETS if bucket <= on_site]
    return max(fitting) if fitting else None
