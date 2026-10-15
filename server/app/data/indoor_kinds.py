"""Kinds of indoor place a parent can like or not (Indoor place setting, story 9.3).

The Vicmap data has one subtype, "sports complex", for every indoor venue, so the
kind is worked out from the venue's name. The rules run in order and the first
match wins, so "Princes Park Carlton Bowls Club" is a club, not a park.
"""

from __future__ import annotations

import re

CLUBS = "clubs"
SWIMMING = "swimming"
INDOOR_SPORTS = "indoor_sports"
RECREATION = "recreation_centre"

# The kinds, in the order the app lists them.
INDOOR_KINDS = (SWIMMING, RECREATION, INDOOR_SPORTS, CLUBS)

_RULES: tuple[tuple[str, re.Pattern], ...] = (
    (CLUBS, re.compile(r"\bclub\b", re.I)),
    (SWIMMING, re.compile(r"\b(pool|baths?|aquatic|swim\w*)\b", re.I)),
    (INDOOR_SPORTS, re.compile(r"\b(stadium|netball|hockey|karting|icehouse|sports centre|tennis centre|womens sports)\b", re.I)),
)


def indoor_kind(name: str | None) -> str:
    """The kind of an indoor place, from its name. Anything that is not clearly a
    club, pool or sports venue is a recreation centre (leisure and community centres)."""
    text = name or ""
    for kind, pattern in _RULES:
        if pattern.search(text):
            return kind
    return RECREATION


def filter_by_kind(places: list, excluded: list[str] | tuple[str, ...]) -> list:
    """Drop places of excluded kinds. Excluding everything falls back to the full list,
    as it does for outdoor places: a parent is never shown nothing because of likes."""
    if not excluded:
        return places
    kept = [p for p in places if p.activity_category not in excluded]
    return kept or places
