from __future__ import annotations

from app.models import DURATION_BUCKETS, DURATION_MIN_BOUNDS



def match_bucket(duration_min: int) -> int:
    """
    Map an input duration to the nearest duration bucket.

    Exact midpoint ties (e.g. 30 -> 20, 50 -> 40) resolve to the smaller bucket.
    """


    
    min_val, max_val = DURATION_MIN_BOUNDS

    if isinstance(duration_min, bool) or not isinstance(duration_min, int):
                raise ValueError(
                    f"Duration must be an integer, got {duration_min!r} ({type(duration_min).__name__})"
                )
        
    if not (min_val <= duration_min <= max_val):
        raise ValueError(
            f"Duration must be between {min_val} and {max_val} minutes, got {duration_min}"
        )
    ValueError(duration_min)
    return min(DURATION_BUCKETS, key=lambda bucket: (abs(duration_min - bucket), bucket))