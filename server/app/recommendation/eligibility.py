"""
Candidate place eligibility filtering.

Evaluates geographic boundaries, search radius limits, classification
confidence thresholds, and template availability to filter valid recommendations.
"""

from __future__ import annotations

from typing import Final, Mapping

from app.models import Place, TravelTime
from app.recommendation.combos import find_combo
from app.recommendation.duration import select_plan_bucket

PILOT_LGAS: Final[frozenset[str]] = frozenset({"melbourne", "melton", "monash"})
MIN_CONFIDENCE: Final[float] = 0.0


def passes_basic_checks(
    place: Place,
    radius_km: int | None,
    min_confidence: float = MIN_CONFIDENCE,
) -> bool:
    """Everything except the time fit: pilot area, radius and confidence."""
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
    return True


def plan_bucket_for(
    place: Place,
    total_min: int,
    travel_times: Mapping[str, TravelTime],
) -> int | None:
    """This place's own plan length, or None if it does not fit.

    The return trip is the outbound time (back_from_outbound), so one
    TravelTime covers both legs. A place with no travel time was dropped
    upstream as unreachable within the total, so it does not fit.
    """
    travel = travel_times.get(place.place_id)
    if travel is None:
        return None
    return select_plan_bucket(total_min, travel.minutes, travel.minutes)


def is_eligible(
    place: Place,
    radius_km: int | None,
    bucket: int,
    min_confidence: float = MIN_CONFIDENCE,
) -> bool:
    if not passes_basic_checks(place, radius_km, min_confidence):
        return False
    return find_combo(place.activity_category, bucket) is not None


def filter_eligible(
    places: tuple[Place, ...],
    radius_km: int | None,
    total_min: int,
    travel_times: Mapping[str, TravelTime],
    min_confidence: float = MIN_CONFIDENCE,
) -> tuple[Place, ...]:
    """Places that pass the basic checks and whose travel out + plan + travel
    back fits within total_min."""
    eligible = []
    for place in places:
        bucket = plan_bucket_for(place, total_min, travel_times)
        if bucket is not None and is_eligible(place, radius_km, bucket, min_confidence):
            eligible.append(place)
    return tuple(eligible)
