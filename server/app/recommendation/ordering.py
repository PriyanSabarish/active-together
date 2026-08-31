"""
Deterministic ranking and ordering for candidate places.

Sorts candidates primarily by tier (normal before deprioritised), followed by
approximate distance, name (named before unnamed, case-insensitively), and
place ID as a deterministic tie-breaker.
"""

from __future__ import annotations

from typing import Final

from app.models import Place, Tier

MAX_COMBOS: Final[int] = 3
TIER_RANK: Final[dict[Tier, int]] = {Tier.NORMAL: 0, Tier.DEPRIORITISED: 1}


def sort_key(place: Place, tier: Tier) -> tuple:
    name_key = (1, "") if place.display_name is None else (0, place.display_name.casefold())
    return (TIER_RANK[tier], place.distance_m, name_key, place.place_id)


def order_candidates(
    places: tuple[Place, ...],
    tier: Tier,
    limit: int = MAX_COMBOS,
) -> tuple[Place, ...]:
    return tuple(sorted(places, key=lambda p: sort_key(p, tier)))[:limit]