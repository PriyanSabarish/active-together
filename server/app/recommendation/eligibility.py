"""
Candidate place eligibility filtering.

Evaluates geographic boundaries, search radius limits, classification
confidence thresholds, and template availability to filter valid recommendations.
"""

from __future__ import annotations

from typing import Final

from app.models import Place
from app.recommendation.combos import find_combo
from app.recommendation.duration import match_bucket

PILOT_LGAS: Final[frozenset[str]] = frozenset({"melbourne", "melton", "monash"})
MIN_CONFIDENCE: Final[float] = 0.0


def is_eligible(
    place: Place,
    radius_km: int | None,
    bucket: int,
    min_confidence: float = MIN_CONFIDENCE,
) -> bool:
    if place.lga_name.lower() not in PILOT_LGAS:
        return False
    if radius_km is not None and place.distance_m > radius_km * 1000:
        return False
    # TODO: classification_confidence currently arrives as a text label
    # ("high"/"medium"/"low") from the pipeline CSV, not the float this
    # compares against. Skip the check until the label->float mapping is
    # decided (see recommendation/README.md open questions) rather than
    # crash or silently coerce a guessed scale.
    if isinstance(place.classification_confidence, (int, float)) and place.classification_confidence < min_confidence:
        return False
    return find_combo(place.activity_category, bucket) is not None


def filter_eligible(
    places: tuple[Place, ...],
    radius_km: int | None,
    duration_min: int,
    min_confidence: float = MIN_CONFIDENCE,
) -> tuple[Place, ...]:
    bucket = match_bucket(duration_min)
    return tuple(
        place
        for place in places
        if is_eligible(place, radius_km, bucket, min_confidence)
    )