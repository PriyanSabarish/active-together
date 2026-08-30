"""
    recommend(candidates, context, duration_min) -> Recommendation
    
assembles the pieces built so far: bucket the duration (B2), assess the
weather (B3, B4), filter for eligibility (B5), order and cap (B6), and return
either combos or a zero-result message (B10).

On radius_km: Backend A's get_candidates already filters by radius, so it
defaults to None and the radius check is skipped. Passing it enables B5's
defensive re-check.
"""

from __future__ import annotations

from typing import Any

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
from app.recommendation.explanation import build_explanation
from app.recommendation.ordering import order_candidates
from app.recommendation.tier import assess

# Story 3.1: the zero-result message suggests a larger radius, a different
# time, or reviewing preferences.
#
# Preference filtering is Epic 4, iteration 2. Until it exists there is no
# preferences screen for a parent to review, so suggesting it would be dead
# advice. The suggestion is written and gated rather than omitted, so
# iteration 2 turns it on by flipping one flag.
PREFERENCES_AVAILABLE = False

SUGGEST_RADIUS = "Try a larger search radius."
SUGGEST_TIME = "Try a different time."
SUGGEST_PREFERENCES = "Review your activity preferences."

# No candidates were passed in at all, or none survived eligibility. The
# distinction is deliberately not surfaced: story 3.1 requires that excluded
# records are not shown, and explaining why one was excluded surfaces it.
ZERO_RESULT_LEAD = "No activities match this search."


def zero_result_message() -> str:
    suggestions = [SUGGEST_RADIUS, SUGGEST_TIME]
    if PREFERENCES_AVAILABLE:
        suggestions.append(SUGGEST_PREFERENCES)
    return " ".join([ZERO_RESULT_LEAD, *suggestions])


def _build_combo(
    place: Place,
    bucket: int,
    duration_min: int,
    tier: Any,
    summary: str,
    timestamp: str | None,
) -> Combo:
    """Assemble one combo card payload (B7), story 3.2.

    Every field is either a verified value from Backend A or a value this
    module derived and can account for. Opening hours, cost, accessibility and
    facilities are absent because Place does not carry them and nothing here
    infers them (B9, story 1.2).
    """
    template = find_combo(place.activity_category, bucket)
    if template is None:
        raise ValueError(
            f"Missing ComboTemplate for category '{place.activity_category}' and bucket {bucket}."
        )

    return Combo(
        place=place,
        activity_type=template.activity_type,
        entered_duration_min=duration_min,
        duration_bucket=bucket,
        combo_template=template.title,
        tier=tier,
        environmental_summary=summary,
        explanation=build_explanation(
            distance_m=place.distance_m,
            entered_duration_min=duration_min,
            bucket=bucket,
            summary=summary,
            timestamp=timestamp,
        ),
    )


def recommend(
    candidates: tuple[Place, ...],
    context: Context,
    duration_min: int,
    radius_km: int | None = None,
    timestamp: str | None = None,
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
            message=zero_result_message(),
        )

    combos = tuple(
        _build_combo(place, bucket, duration_min, tier, summary, timestamp)
        for place in ordered
    )

    # Fewer than three returns what exists — the cap in order_candidates
    # truncates but never pads (B11).
    return Recommendation(status=RecommendationStatus.OK, combos=combos)