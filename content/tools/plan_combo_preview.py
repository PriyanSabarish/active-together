"""Print a development-only combo timetable for explicitly selected activity IDs."""

import argparse
import json
import sys
from pathlib import Path

from jsonschema.exceptions import SchemaError

# Allow direct execution from any working directory.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from content.tools.activity_library import AGE_BANDS
from content.tools.combo_planning import build_combo_preview


def main():
    """Parse a chosen set and export a timetable without changing activity files."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--activity-id", action="append", required=True, help="Repeat for each chosen activity, in order.")
    parser.add_argument("--age-band", choices=AGE_BANDS, required=True)
    parser.add_argument("--duration", type=int, choices=[20, 40, 60], required=True)
    parser.add_argument("--output", type=Path, help="Optional .json path; otherwise print JSON.")
    args = parser.parse_args()
    try:
        if args.output and args.output.suffix.lower() != ".json":
            raise ValueError("Output must use a .json extension.")
        plan = build_combo_preview(args.activity_id, args.age_band, args.duration)
        text = json.dumps(plan, ensure_ascii=False, indent=2) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(text, encoding="utf-8")
            print(f"Wrote development plan: {plan['status']} ({plan['scheduled_minutes']} minutes).")
        else:
            print(text, end="")
    except (OSError, ValueError, SchemaError) as error:
        parser.exit(1, f"Combo preview failed: {error}\n")


if __name__ == "__main__":
    main()
