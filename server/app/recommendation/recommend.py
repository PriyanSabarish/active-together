"""
Recommendation pipeline orchestration.

Combines duration bucketing, environmental threshold assessment, eligibility
filtering, and candidate ranking to produce activity recommendation combos.
"""

from __future__ import annotations

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