"""Club places for the Indoor place list (story 9.3).

content/indoor/club_places.csv is a copy of data/club_places.csv (the team's "indoor places"
file, filtered from the places dataset). The server image is built from server/ alone, so it
cannot read the repo's data/ folder; a test keeps the two copies identical.

Only real clubs are used: the Turf Club walkways, reserve and playground in that file are
places that happen to have "Turf Club" in the name, not clubs.
"""

from __future__ import annotations

import csv
from functools import lru_cache
from pathlib import Path

CLUB_PLACES_PATH = Path(__file__).resolve().parents[2] / "content" / "indoor" / "club_places.csv"
NOT_CLUBS = ("Turf Club",)


@lru_cache(maxsize=1)
def club_place_names() -> tuple[str, ...]:
    with open(CLUB_PLACES_PATH, newline="", encoding="utf-8-sig") as f:
        names = [row["place_name"].strip() for row in csv.DictReader(f) if row.get("place_name")]
    return tuple(sorted({n for n in names if not any(bad in n for bad in NOT_CLUBS)}))
