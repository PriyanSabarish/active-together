"""
    recommend(candidates, context, total_min, travel_times, mode) -> Recommendation

assembles the pieces built so far: pick each place's plan length from the
time left after travel (B48), assess the
weather (B3, B4), filter for eligibility (B5), order and cap (B6), and return
either combos or a zero-result message (B10).

On radius_km: Backend A's get_candidates already filters by radius, so it
defaults to None and the radius check is skipped. Passing it enables B5's
defensive re-check.
"""

from __future__ import annotations

from typing import Any, Mapping

from app.models import (
    ActivityCategory,
    Combo,
    Context,
    Place,
    DURATION_BUCKETS,
    DURATION_MIN_BOUNDS,
    Recommendation,
    RecommendationStatus,
    Suggestion,
    SuggestionKind,
    Tier,
    TravelBlock,
    TravelMode,
    TravelTime,
)
from app.recommendation.combos import find_combo
from app.recommendation.eligibility import (
    MIN_CONFIDENCE,
    filter_eligible,
    passes_basic_checks,
    plan_bucket_for,
)
from app.recommendation.explanation import build_explanation
from app.recommendation.ordering import order_candidates, sort_key
from app.recommendation.preferences import filter_by_preference
from app.recommendation.tier import assess

# Story 3.1: the zero-result message suggests a larger radius, a different
# time, or reviewing preferences.
#
# Preference filtering is Epic 4, iteration 2 (B28). Now that
# filter_by_preference exists and recommend() applies it, the suggestion is
# no longer dead advice.
PREFERENCES_AVAILABLE = True

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


# Zero-result suggestions (B50, decision D8): "more time" names the smallest
# total that fits the nearest place and counts what fits at that total;
# "another mode" names a faster mode and carries no count, because Backend B
# holds travel times for the requested mode only.
FASTER_MODE: dict[TravelMode, TravelMode] = {
    TravelMode.WALKING: TravelMode.CYCLING,
    TravelMode.CYCLING: TravelMode.DRIVING,
}


def suggest_next_steps(
    places: tuple[Place, ...],
    total_min: int,
    mode: TravelMode,
    travel_times: Mapping[str, TravelTime],
) -> tuple[Suggestion, ...]:
    """Suggestions for a search with no fit.

    places must already be filtered on everything except time (area, radius,
    confidence, preferences), so a place excluded for another reason is never
    named or counted. Order within the nearest-place choice follows D17.
    """
    suggestions: list[Suggestion] = []

    reachable = [p for p in places if p.place_id in travel_times]
    if reachable:
        nearest = min(reachable, key=lambda p: sort_key(p, Tier.NORMAL))
        trip = travel_times[nearest.place_id].minutes
        smallest_total = 2 * trip + min(DURATION_BUCKETS)
        if total_min < smallest_total <= DURATION_MIN_BOUNDS[1]:
            fits_count = sum(
                1 for p in reachable if plan_bucket_for(p, smallest_total, travel_times) is not None
            )
            suggestions.append(
                Suggestion(SuggestionKind.MORE_TIME, total_min=smallest_total, fits_count=fits_count)
            )

    faster = FASTER_MODE.get(mode)
    if faster is not None:
        suggestions.append(Suggestion(SuggestionKind.OTHER_MODE, mode=faster))

    return tuple(suggestions)


def _build_combo(
    place: Place,
    bucket: int,
    total_min: int,
    travel_time: TravelTime,
    mode: TravelMode,
    tier: Any,
    summary: str,
    timestamp: str | None,
) -> Combo:
    """Assemble one combo card payload (B7), story 3.2.

    Every field is either a verified value from Backend A or a value this
    module derived and can account for. Opening hours, cost, accessibility and
    facilities are absent because Place does not carry them and nothing here
    infers them (B9, story 1.2).

    bucket is this place's own plan length; other combos in the same result
    can differ.
    """
    template = find_combo(place.activity_category, bucket)
    if template is None:
        raise ValueError(
            f"Missing ComboTemplate for category '{place.activity_category}' and bucket {bucket}."
        )

    travel = TravelBlock(
        mode=mode,
        out_min=travel_time.minutes,
        back_min=travel_time.minutes,
        on_site_min=bucket,
        total_min=2 * travel_time.minutes + bucket,
        source=travel_time.source,
        back_from_outbound=True,
    )

    return Combo(
        combo_id=place.place_id,
        place=place,
        activity_type=template.activity_type,
        entered_duration_min=total_min,
        duration_bucket=bucket,
        combo_template=template.title,
        tier=tier,
        environmental_summary=summary,
        explanation=build_explanation(
            distance_m=place.distance_m,
            entered_total_min=total_min,
            travel=travel,
            summary=summary,
            timestamp=timestamp,
        ),
        travel=travel,
    )


def recommend(
    candidates: tuple[Place, ...],
    context: Context,
    total_min: int,
    travel_times: Mapping[str, TravelTime],
    mode: TravelMode = TravelMode.WALKING,
    radius_km: int | None = None,
    timestamp: str | None = None,
    min_confidence: float = MIN_CONFIDENCE,
    excluded_categories: tuple[ActivityCategory, ...] = (),
) -> Recommendation:
    tier, summary = assess(context)

    in_scope = tuple(
        p
        for p in filter_by_preference(candidates, excluded_categories)
        if passes_basic_checks(p, radius_km, min_confidence)
    )
    eligible = filter_eligible(
        in_scope,
        radius_km=radius_km,
        total_min=total_min,
        travel_times=travel_times,
        min_confidence=min_confidence,
    )
    # Straight-line distance, then name, is unchanged by travel time (D17).
    ordered = order_candidates(eligible, tier)

    if not ordered:
        return Recommendation(
            status=RecommendationStatus.ZERO_RESULTS,
            combos=(),
            message=zero_result_message(),
            suggestions=suggest_next_steps(in_scope, total_min, mode, travel_times),
        )

    combos = tuple(
        _build_combo(
            place,
            plan_bucket_for(place, total_min, travel_times),
            total_min,
            travel_times[place.place_id],
            mode,
            tier,
            summary,
            timestamp,
        )
        for place in ordered
    )

    # Fewer than three returns what exists — the cap in order_candidates
    # truncates but never pads (B11).
    return Recommendation(status=RecommendationStatus.OK, combos=combos)
