"""
Recommendation pipeline orchestration.

Evaluates activity duration, environmental conditions, and place eligibility
to generate ranked activity recommendations or provide fallback guidance when
no matching candidates are found.
"""

from __future__ import annotations

from typing import Final

from app.models import (
    Combo,
    Context,
    Place,
    Recommendation,
    RecommendationStatus,
)
from app.recommendation.combos import find_combo
from app.recommendation.duration import match_bucket
from app.recommendation.eligibility import MIN_CONFIDENCE, filter_eligible
from app.recommendation.ordering import order_candidates
from app.recommendation.tier import assess

PREFERENCES_AVAILABLE: Final[bool] = False

ZERO_RESULT_LEAD: Final[str] = "No activities match this search."
SUGGEST_RADIUS: Final[str] = "Try a larger search radius."
SUGGEST_TIME: Final[str] = "Try a different time."
SUGGEST_PREFERENCES: Final[str] = "Review your activity preferences."


def build_zero_result_message() -> str:
    suggestions = [SUGGEST_RADIUS, SUGGEST_TIME]
    if PREFERENCES_AVAILABLE:
        suggestions.append(SUGGEST_PREFERENCES)
    return f"{ZERO_RESULT_LEAD} {' '.join(suggestions)}"


def recommend(
    candidates: tuple[Place, ...],
    context: Context,
    duration_min: int,
    radius_km: int | None = None,
    min_confidence: float = MIN_CONFIDENCE,
) -> Recommendation:
    bucket = match_bucket(duration_min)
    tier, summary = assess(context)

    eligible = filter_eligible(
        candidates,
        radius_km=radius_km,
        duration_min=duration_min,
        min_confidence=min_confidence,
    )
    ordered = order_candidates(eligible, tier)

    if not ordered:
        return Recommendation(
            status=RecommendationStatus.ZERO_RESULTS,
            combos=(),
            message=build_zero_result_message(),
        )

    combos = tuple(
        Combo(
            place=place,
            activity_type=place.activity_category.value,
            entered_duration_min=duration_min,
            duration_bucket=bucket,
            combo_template=find_combo(place.activity_category, bucket) or "",
            tier=tier,
            environmental_summary=summary,
            explanation="",
        )
        for place in ordered
    )

    return Recommendation(status=RecommendationStatus.OK, combos=combos)