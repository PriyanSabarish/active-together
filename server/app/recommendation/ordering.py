"""
Deterministic ranking and ordering for candidate places.

Sorts candidates primarily by tier (normal before deprioritised), followed by
approximate distance, name (named before unnamed, case-insensitively), and
place ID as a deterministic tie-breaker.
"""

from __future__ import annotations

from typing import Final, Mapping

from app.config import settings
from app.models import Place, Tier

MAX_COMBOS: Final[int] = 3
TIER_RANK: Final[dict[Tier, int]] = {Tier.NORMAL: 0, Tier.DEPRIORITISED: 1}


def sort_key(place: Place, tier: Tier) -> tuple:
    name_key = (1, "") if place.display_name is None else (0, place.display_name.casefold())
    return (TIER_RANK[tier], place.distance_m, name_key, place.place_id)


def select_nearest(
    places: tuple[Place, ...],
    tier: Tier,
    limit: int = MAX_COMBOS,
) -> tuple[Place, ...]:
    """The original rule: sort by sort_key and take the first `limit`."""
    return tuple(sorted(places, key=lambda p: sort_key(p, tier)))[:limit]


# Kept as the public name the rest of the code (and its tests) already use.
order_candidates = select_nearest


# --- Spread mode -----------------------------------------------------------


def band_edges(limit_min: int, band_count: int) -> list[tuple[float, float]]:
    """Equal slices of the travel limit: 30 min, 3 bands -> (0,10], (10,20], (20,30]."""
    width = limit_min / band_count
    return [(i * width, (i + 1) * width) for i in range(band_count)]


def band_of(travel_min: float, edges: list[tuple[float, float]]) -> int:
    """Index of the band a travel time falls in. A value exactly on an edge goes
    to the lower band; anything past the last edge is clamped to the last band."""
    for i, (_, high) in enumerate(edges):
        if travel_min <= high:
            return i
    return len(edges) - 1


def pick_varied(
    pool: list[Place],
    tier: Tier,
    seen_categories: set,
) -> Place | None:
    """First place by sort_key whose category is unseen; failing that, the first
    by sort_key; None if the pool is empty. Never excludes anything."""
    if not pool:
        return None
    ordered = sorted(pool, key=lambda p: sort_key(p, tier))
    for place in ordered:
        if place.activity_category not in seen_categories:
            return place
    return ordered[0]


def select_spread(
    places: tuple[Place, ...],
    tier: Tier,
    travel_min_of: Mapping[str, float],
    limit_min: int,
    n: int = MAX_COMBOS,
    band_count: int | None = None,
    min_band_width_min: int | None = None,
) -> tuple[Place, ...]:
    """Pick up to n places spread across the travel range and activity kinds.

    Priority: tier -> distance band -> unseen category -> sort_key. A band is
    never skipped to get a new category, and category variety never removes a
    place. Chosen places are returned in sort_key order.

    Every place must have an entry in travel_min_of. The tier is the same for
    every candidate (it comes from the weather), so "normal first" and
    "deprioritised fills leftovers" only matters when tiers are mixed; here the
    given tier applies to the whole set.
    """
    band_count = band_count if band_count is not None else settings.travel_spread_band_count
    min_width = (
        min_band_width_min if min_band_width_min is not None else settings.travel_spread_min_band_width_min
    )

    if len(places) <= n:
        return tuple(sorted(places, key=lambda p: sort_key(p, tier)))

    remaining = list(places)
    picked: list[Place] = []
    seen: set = set()

    def take(place: Place | None) -> bool:
        if place is None:
            return False
        picked.append(place)
        remaining.remove(place)
        seen.add(place.activity_category)
        return True

    if limit_min / band_count >= min_width:
        edges = band_edges(limit_min, band_count)
        # One per band, near to far.
        for band in range(band_count):
            if len(picked) >= n:
                break
            pool = [p for p in remaining if band_of(travel_min_of[p.place_id], edges) == band]
            take(pick_varied(pool, tier, seen))
    else:
        # Bands too narrow: category variety only, nearest of each unseen kind.
        while len(picked) < n and any(p.activity_category not in seen for p in remaining):
            take(pick_varied(remaining, tier, seen))

    # Backfill: unseen kinds first, then nearest.
    while len(picked) < n and remaining:
        take(pick_varied(remaining, tier, seen))

    return tuple(sorted(picked, key=lambda p: sort_key(p, tier)))