"""Export reviewed activities as JSON; drafts require explicit --preview."""

import argparse
import json
from pathlib import Path

from jsonschema.exceptions import SchemaError

from activity_library import AGE_BANDS, build_export


def main():
    """Validate, optionally filter, then print JSON or save it to --output."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preview", action="store_true", help="Allow development drafts.")
    parser.add_argument("--activity-type", help="Exact activity type; no match returns an empty list.")
    parser.add_argument("--age-band", choices=AGE_BANDS, help="Require this age variant.")
    parser.add_argument("--output", type=Path, help="Write a .json file instead of printing JSON.")
    args = parser.parse_args()
    try:
        if args.output and args.output.suffix.lower() != ".json":
            raise ValueError("Output must use a .json extension.")
        payload = build_export(args.preview, args.activity_type, args.age_band)
        text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(text, encoding="utf-8")
            print(f"Wrote {len(payload['activities'])} activities ({payload['mode']}) to {args.output}")
        else:
            print(text, end="")
    except (OSError, ValueError, SchemaError) as error:
        parser.exit(1, f"Activity export failed: {error}\n")


if __name__ == "__main__":
    main()
