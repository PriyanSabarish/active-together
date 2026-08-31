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

PILOT_LGAS: Final[frozenset[str]] = frozenset({"Melbourne", "Melton", "Monash"})
MIN_CONFIDENCE: Final[float] = 0.0


def is_eligible(
    place: Place,
    radius_km: int | None,
    bucket: int,
    min_confidence: float = MIN_CONFIDENCE,
) -> bool:
    if place.lga_name not in PILOT_LGAS:
        return False
    if radius_km is not None and place.distance_m > radius_km * 1000:
        return False
    if place.classification_confidence < min_confidence:
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