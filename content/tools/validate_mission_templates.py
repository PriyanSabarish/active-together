"""Check the migrated mission collection; draft content requires --preview."""

import argparse
from pathlib import Path
import sys

from jsonschema.exceptions import SchemaError

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from content.tools.mission_context import load_context_bindings
from content.tools.mission_library import load_mission_families


def main():
    """Print family, age and bucket coverage plus actionable content warnings."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preview", action="store_true")
    args = parser.parse_args()
    try:
        families, warnings = load_mission_families(args.preview)
        load_context_bindings(families)
        bands = sum(len(item["bands"]) for item in families)
        combinations = sum(len(item["bands"]) * (item["duration_bucket"] // 20) for item in families)
        mode = "development preview" if args.preview else "reviewed"
        print(f"Valid {mode}: {len(families)} families, {bands} age variants, {combinations} band/bucket combinations.")
        for warning in warnings:
            print("WARNING: " + warning)
        print("Checks include the nine safety rules; human review and timing measurement remain required.")
    except (ValueError, SchemaError) as error:
        parser.exit(1, f"Mission validation failed: {error}\n")


if __name__ == "__main__":
    main()
