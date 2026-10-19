"""Build server/content/indoor/indoor_places.csv from the places data (story 9.3).

Usage:  python scripts/build_indoor_file.py            (from server/)
        python scripts/build_indoor_file.py --csv ../data/vicmap_app_ready.csv

Keeps the rows the Indoor place setting lists: the "sports complex" rows less stadiums and
unnamed sites, plus the club places in content/indoor/club_places.csv. The server reads this
file first, so run this and commit the result whenever data/vicmap_app_ready.csv or the club
list changes. A test fails if the file is out of step with the data.
"""

import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.data.club_places import club_place_names
from app.data.indoor_file import COLUMNS, INDOOR_FILE_PATH
from app.data.places import INDOOR_EXCLUDED_NAMES, INDOOR_SUBTYPE

DEFAULT_CSV = Path(__file__).resolve().parent.parent.parent / "data" / "vicmap_app_ready.csv"


def build_rows(csv_path: Path) -> list[dict]:
    clubs = set(club_place_names())
    out = []
    with open(csv_path, newline="", encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            if r["decision"] != "include":
                continue
            name = r["display_name"]
            sports_complex = (
                r["feature_subtype"] == INDOOR_SUBTYPE
                and name not in INDOOR_EXCLUDED_NAMES
                and not name.startswith("Unnamed ")
            )
            if not (sports_complex or name in clubs):
                continue
            out.append({
                "place_id": r["place_id"],
                "display_name": name,
                "lga_name": r["lga_name"],
                "latitude": r["latitude"],
                "longitude": r["longitude"],
                "classification_confidence": r["classification_confidence"],
            })
    out.sort(key=lambda x: x["place_id"])
    return out


def write_file(rows: list[dict], path: Path = INDOOR_FILE_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--csv", default=str(DEFAULT_CSV))
    args = parser.parse_args()
    rows = build_rows(Path(args.csv))
    write_file(rows)
    print(f"Wrote {len(rows)} indoor places to {INDOOR_FILE_PATH}")


if __name__ == "__main__":
    main()
