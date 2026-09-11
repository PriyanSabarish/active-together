"""Report activity content coverage and gaps in the proposed subtype mappings."""

import argparse
from collections import Counter
from pathlib import Path
import sys

from jsonschema.exceptions import SchemaError

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from content.tools.activity_library import AGE_BANDS, CONTENT_DIR, load_preview_activities, read_yaml
from content.tools.combo_planning import load_duration_rules


def build_coverage_report(content_dir=CONTENT_DIR):
    """Count draft and reviewed content without claiming actual site suitability."""
    content_dir = Path(content_dir)
    activities = load_preview_activities(content_dir)
    taxonomy = read_yaml(content_dir / "taxonomy/activity_types.yaml")
    mapping = read_yaml(content_dir / "taxonomy/subtype_activity_mapping.yaml")
    config, profiles = load_duration_rules(activities, content_dir)
    type_ids = [item["id"] for item in taxonomy["activity_types"]]
    counts = Counter(item["activity_type"] for item in activities)
    reviewed = [item for item in activities if item["review"]["status"] == "reviewed"]
    reviewed_counts = Counter(item["activity_type"] for item in reviewed)
    variants = sum(len(item["age_variants"]) for item in activities)
    lines = ["# Activity coverage report", "",
             f"{len(activities)} activities; {variants} age variants; {len(reviewed)} reviewed activities.",
             f"{sum(not item['equipment']['required'] for item in activities)} activities need no equipment.",
             "Generated from the current content files. Counts are not field-test evidence.", "",
             "| Activity type | Draft | Reviewed | 5-7 | 8-10 | 11-12 |",
             "| --- | ---: | ---: | ---: | ---: | ---: |"]
    for type_id in type_ids:
        group = [item for item in activities if item["activity_type"] == type_id]
        ages = [sum(band in item["age_variants"] for item in group) for band in AGE_BANDS]
        lines.append(f"| {type_id} | {counts[type_id] - reviewed_counts[type_id]} | {reviewed_counts[type_id]} | "
                     + " | ".join(str(count) for count in ages) + " |")
    lines.extend(["", "## Proposed location mapping coverage", "",
                  "These are type-level content shortlists, not approved matches to real places.",
                  "Every activity's requirements still apply. Draft and reviewed counts do not",
                  "establish available equipment, access, suitable surfaces or actual place coverage.",
                  f"Place counts use `{mapping['source']['path']}` at `{mapping['source']['git_commit']}`.", "",
                  "| Category | Subtype | Source places | Content candidates | Reviewed candidates |",
                  "| --- | --- | ---: | ---: | ---: |"])
    seen = set()
    gap_places = 0
    for row in mapping["mappings"]:
        key = (row["activity_category"], row["feature_type"], row["feature_subtype"])
        if key in seen:
            raise ValueError("Duplicate subtype mapping: " + str(key))
        seen.add(key)
        types = row["candidate_activity_types"]
        if len(types) != len(set(types)) or not set(types).issubset(type_ids):
            raise ValueError("Invalid activity types in mapping: " + str(key))
        count = sum(counts[item] for item in types)
        approved_count = sum(reviewed_counts[item] for item in types)
        if count == 0:
            gap_places += row["source_count"]
        lines.append(f"| {row['activity_category']} | {row['feature_subtype']} | {row['source_count']} | {count} | {approved_count} |")
    if sum(row["source_count"] for row in mapping["mappings"]) != mapping["source"]["record_count"]:
        raise ValueError("Mapping counts do not match the recorded source total.")
    missing_types = [item for item in type_ids if counts[item] == 0]
    lines.extend(["", "## Gaps and timing", "",
                  "Types without authored content: " + (", ".join(missing_types) or "none") + ".",
                  f"Subtype rows with no content candidates account for {gap_places} source places.",
                  "There is no automatic generic fallback for these gaps.",
                  f"Duration profiles: {len(profiles)}; timing basis: `{config['timing_basis']}`.",
                  "Timing values and 20/40/60-minute previews are development estimates, not measured durations.",
                  "A 60-minute request can return unused time; activities are not stretched to fill it.",
                  "Independent review, practical timing and receiving-app integration remain outstanding.", ""])
    return "\n".join(lines)


def main():
    """Print the report or save it to a requested Markdown path."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        if args.output and args.output.suffix.lower() != ".md":
            raise ValueError("Report output must use a .md extension.")
        report = build_coverage_report()
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(report, encoding="utf-8")
            print("Wrote coverage report to " + str(args.output))
        else:
            print(report, end="")
    except (OSError, ValueError, SchemaError) as error:
        parser.exit(1, f"Coverage report failed: {error}\n")


if __name__ == "__main__":
    main()
