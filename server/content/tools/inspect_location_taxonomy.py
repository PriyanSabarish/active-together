"""Print a read-only inventory of the location CSV using Python 3.10+."""

import argparse
import csv
import io
import json
import subprocess
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATH = "data/vicmap_app_ready.csv"
MATCH_FIELDS = ("activity_category", "feature_type", "feature_subtype")


def git_output(*arguments):
    """Read Git output from this repository without changing its state."""
    result = subprocess.run(
        ["git", "-C", str(ROOT), *arguments],
        check=True, capture_output=True, encoding="utf-8",
    )
    return result.stdout.strip()


def read_source(ref):
    """Read the published CSV from a local commit or the working copy."""
    source = {"path": SOURCE_PATH}
    if ref:
        commit = git_output("rev-parse", "--verify", "--end-of-options", ref + "^{commit}")
        source["git_commit"] = commit
        source["git_blob"] = git_output("rev-parse", commit + ":" + SOURCE_PATH)
        text = git_output("show", commit + ":" + SOURCE_PATH)
    else:
        source["version"] = "working_copy"
        text = (ROOT / SOURCE_PATH).read_text(encoding="utf-8-sig")

    reader = csv.DictReader(io.StringIO(text.lstrip("\ufeff")))
    required = {"place_id", *MATCH_FIELDS}
    if not required.issubset(reader.fieldnames or []):
        raise ValueError("CSV must contain place_id and all three classification fields.")
    rows = list(reader)
    if not rows:
        raise ValueError("The location CSV has no records.")
    ids = set()
    for row in rows:
        if any(not (row.get(field) or "").strip() for field in required):
            raise ValueError("A location has an empty identity or classification field.")
        if row["place_id"] in ids:
            raise ValueError("Duplicate place_id: " + row["place_id"])
        ids.add(row["place_id"])
    return source, rows


def build_inventory(source, rows):
    """Count exact category/type/subtype combinations for mapping review."""
    counts = Counter(tuple(row[field] for field in MATCH_FIELDS) for row in rows)
    combinations = []
    for values, count in sorted(counts.items()):
        item = dict(zip(MATCH_FIELDS, values))
        item["source_count"] = count
        combinations.append(item)
    return {
        "source": source,
        "record_count": len(rows),
        "category_count": len({row["activity_category"] for row in rows}),
        "combination_count": len(combinations),
        "combinations": combinations,
    }


def main():
    """Parse the optional local Git reference and print the inventory as JSON."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ref", help="Local Git commit or branch; omit for working-copy data.")
    args = parser.parse_args()
    try:
        source, rows = read_source(args.ref)
        print(json.dumps(build_inventory(source, rows), indent=2))
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        parser.exit(1, "Could not inspect location data: " + str(error) + "\n")


if __name__ == "__main__":
    main()
