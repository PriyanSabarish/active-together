"""Indoor places read from a file shipped with the server (story 9.3).

content/indoor/indoor_places.csv holds the indoor rows of the places data: the "sports
complex" rows (less stadiums and unnamed sites) and the club places. It is built from
data/vicmap_app_ready.csv by scripts/build_indoor_file.py, and a test keeps the two in step.

Reading it needs no database, so the Indoor place setting still works when the places
table is missing, empty or loaded from older data. app/data/places.py uses this first and
falls back to the database only when the file cannot be read.
"""

from __future__ import annotations

import csv
import math
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

INDOOR_FILE_PATH = Path(__file__).resolve().parents[2] / "content" / "indoor" / "indoor_places.csv"
COLUMNS = ("place_id", "display_name", "lga_name", "latitude", "longitude", "classification_confidence")

EARTH_RADIUS_M = 6371008.8


@dataclass(frozen=True)
class IndoorRow:
    place_id: str
    display_name: str
    lga_name: str
    latitude: float
    longitude: float
    classification_confidence: str | None


@lru_cache(maxsize=1)
def indoor_rows() -> tuple[IndoorRow, ...]:
    """Every row in the file. Raises if the file is missing or malformed; the caller
    treats that as 'file unavailable' and uses the database."""
    with open(INDOOR_FILE_PATH, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        missing = set(COLUMNS) - set(reader.fieldnames or ())
        if missing:
            raise ValueError(f"indoor_places.csv is missing columns: {sorted(missing)}")
        rows = tuple(
            IndoorRow(
                place_id=r["place_id"],
                display_name=r["display_name"],
                lga_name=r["lga_name"],
                latitude=float(r["latitude"]),
                longitude=float(r["longitude"]),
                classification_confidence=r["classification_confidence"] or None,
            )
            for r in reader
        )
    if not rows:
        raise ValueError("indoor_places.csv has no rows")
    return rows


def distance_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in metres (haversine)."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * EARTH_RADIUS_M * math.asin(math.sqrt(a))


def rows_within(lat: float, lon: float, radius_km: float | None) -> list[tuple[IndoorRow, float]]:
    """(row, distance in metres) for each row inside the radius, nearest first, then by name.
    A radius of None means no limit: every row, nearest first."""
    radius_m = None if radius_km is None else radius_km * 1000.0
    found = []
    for row in indoor_rows():
        d = distance_m(lat, lon, row.latitude, row.longitude)
        if radius_m is None or d <= radius_m:
            found.append((row, d))
    found.sort(key=lambda x: (x[1], x[0].display_name))
    return found
