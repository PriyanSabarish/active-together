"""Load indoor places into the indoor_places table (story 9.3, task A53).

Usage:  python scripts/load_indoor_places.py --csv ../data/indoor_places.csv

The CSV has one row per place with the columns in REQUIRED_COLUMNS. Rows whose
category is not in INDOOR_CATEGORIES are rejected rather than loaded, so a typo
cannot put an unknown category in front of a parent. Re-running updates rows in
place (keyed on place_id).

INDOOR_CATEGORIES is provisional: which categories count as indoor, and which
file they come from, is still an open item with Data (backend plan section 9).
"""

import argparse
import csv
import sys
from pathlib import Path

from sqlalchemy import create_engine, text

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.config import get_settings

INDOOR_CATEGORIES = frozenset({
    "library",
    "leisure_centre",
    "indoor_play",
    "community_hall",
})

REQUIRED_COLUMNS = {
    "place_id", "display_name", "activity_category", "lga_name",
    "longitude", "latitude",
}
OPTIONAL_COLUMNS = (
    "classification_confidence", "feature_type", "feature_subtype",
    "source_dataset", "source_record_id",
)

INSERT_SQL = text("""
    INSERT INTO indoor_places (
        place_id, display_name, activity_category, classification_confidence,
        lga_name, feature_type, feature_subtype, source_dataset,
        source_record_id, location
    )
    VALUES (
        :place_id, :display_name, :activity_category, :classification_confidence,
        :lga_name, :feature_type, :feature_subtype, :source_dataset,
        :source_record_id, ST_SetSRID(ST_MakePoint(:longitude, :latitude), 4326)
    )
    ON CONFLICT (place_id) DO UPDATE SET
        display_name = EXCLUDED.display_name,
        activity_category = EXCLUDED.activity_category,
        classification_confidence = EXCLUDED.classification_confidence,
        lga_name = EXCLUDED.lga_name,
        feature_type = EXCLUDED.feature_type,
        feature_subtype = EXCLUDED.feature_subtype,
        source_dataset = EXCLUDED.source_dataset,
        source_record_id = EXCLUDED.source_record_id,
        location = EXCLUDED.location
""")


def load_rows(csv_path: Path, categories=INDOOR_CATEGORIES):
    """Parse the CSV. Returns (rows, rejected) where rejected is a list of
    (line_number, reason). Nothing is written here."""
    with open(csv_path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        missing = REQUIRED_COLUMNS - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"CSV missing columns: {sorted(missing)}")

        rows, rejected, seen = [], [], set()
        for line, row in enumerate(reader, start=2):
            place_id = (row["place_id"] or "").strip()
            name = (row["display_name"] or "").strip()
            category = (row["activity_category"] or "").strip()
            if not place_id or not name:
                rejected.append((line, "missing place_id or display_name"))
                continue
            if category not in categories:
                rejected.append((line, f"category {category!r} is not an indoor category"))
                continue
            if place_id in seen:
                rejected.append((line, f"duplicate place_id {place_id!r}"))
                continue
            try:
                lon, lat = float(row["longitude"]), float(row["latitude"])
            except (TypeError, ValueError):
                rejected.append((line, "longitude or latitude is not a number"))
                continue
            if not (-180 <= lon <= 180 and -90 <= lat <= 90):
                rejected.append((line, "coordinates out of range"))
                continue
            seen.add(place_id)
            rows.append({
                "place_id": place_id,
                "display_name": name,
                "activity_category": category,
                "lga_name": (row["lga_name"] or "").strip(),
                "longitude": lon,
                "latitude": lat,
                **{c: (row.get(c) or "").strip() or None for c in OPTIONAL_COLUMNS},
            })
        return rows, rejected


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", default="../data/indoor_places.csv")
    args = parser.parse_args()

    csv_path = Path(args.csv)
    if not csv_path.exists():
        print(f"CSV not found: {csv_path}")
        sys.exit(1)

    rows, rejected = load_rows(csv_path)
    print(f"parsed {len(rows)} rows to load, {len(rejected)} rejected")
    for line, reason in rejected[:20]:
        print(f"  line {line}: {reason}")
    if not rows:
        print("nothing to load")
        sys.exit(1)

    engine = create_engine(get_settings().database_url)
    with engine.begin() as conn:
        for row in rows:
            conn.execute(INSERT_SQL, row)

    print(f"loaded {len(rows)} rows into indoor_places")


if __name__ == "__main__":
    main()
