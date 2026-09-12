"""Check activity files; add --preview to include development drafts."""

import argparse

from jsonschema.exceptions import SchemaError

from activity_library import load_preview_activities, load_reviewed_activities


def main():
    """Validate the selected library and report activity and age-variant counts."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preview", action="store_true", help="Also check candidate drafts.")
    args = parser.parse_args()
    try:
        activities = load_preview_activities() if args.preview else load_reviewed_activities()
        variant_count = sum(len(activity["age_variants"]) for activity in activities)
        mode = "development preview" if args.preview else "reviewed"
        print(f"Valid {mode}: {len(activities)} activities, {variant_count} age variants.")
        print("Structure checks do not replace human content review.")
        print("Legacy authoring format: use validate_mission_templates.py for the migrated contract and safety checks.")
    except (ValueError, SchemaError) as error:
        parser.exit(1, f"Activity validation failed: {error}\n")


if __name__ == "__main__":
    main()
