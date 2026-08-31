"""Load and validate the three pilot LGA representative points."""

from __future__ import annotations

import csv
from pathlib import Path

from .models import Location


DEFAULT_LOCATIONS_PATH = Path(__file__).parent / "config" / "pilot_locations.csv"
EXPECTED_SITES = {"melton", "melbourne", "monash"}


def load_locations(path: Path = DEFAULT_LOCATIONS_PATH) -> dict[str, Location]:
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    locations = {
        row["site_name"]: Location(
            lga_code=row["lga_code"],
            site_name=row["site_name"],
            display_name=row["display_name"],
            latitude=float(row["latitude"]),
            longitude=float(row["longitude"]),
        )
        for row in rows
    }
    if set(locations) != EXPECTED_SITES:
        raise ValueError(
            f"Pilot locations must be exactly {sorted(EXPECTED_SITES)}; "
            f"found {sorted(locations)}"
        )
    if len({item.lga_code for item in locations.values()}) != len(locations):
        raise ValueError("Pilot lga_code values must be unique")
    return locations
