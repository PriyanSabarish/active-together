import argparse
import csv
import sys
from pathlib import Path

from sqlalchemy import create_engine, text

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.config import get_settings

REQUIRED_COLUMNS = {
    "place_id", "display_name", "activity_category",
    "classification_confidence", "lga_name", "longitude", "latitude",
    "feature_type", "feature_subtype", "decision", "source_dataset",
    "source_record_id",
}

INSERT_SQL = text("""
    INSERT INTO places (
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


def load_rows(csv_path: Path):
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        missing = REQUIRED_COLUMNS - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"CSV missing columns: {missing}")

        rows = []
        skipped = 0
        for row in reader:
            if row["decision"] != "include":
                skipped += 1
                continue
            rows.append({
                "place_id": row["place_id"],
                "display_name": row["display_name"],
                "activity_category": row["activity_category"],
                "classification_confidence": row["classification_confidence"],
                "lga_name": row["lga_name"],
                "feature_type": row["feature_type"],
                "feature_subtype": row["feature_subtype"],
                "source_dataset": row["source_dataset"],
                "source_record_id": row["source_record_id"],
                "longitude": float(row["longitude"]),
                "latitude": float(row["latitude"]),
            })
        return rows, skipped


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", default="../data/vicmap_app_ready.csv")
    args = parser.parse_args()

    csv_path = Path(args.csv)
    if not csv_path.exists():
        print(f"CSV not found: {csv_path}")
        sys.exit(1)

    rows, skipped = load_rows(csv_path)
    print(f"parsed {len(rows)} rows to load, {skipped} skipped (decision != include)")

    settings = get_settings()
    engine = create_engine(settings.database_url)

    with engine.begin() as conn:
        for row in rows:
            conn.execute(INSERT_SQL, row)

    print(f"loaded {len(rows)} rows into place")


if __name__ == "__main__":
    main()