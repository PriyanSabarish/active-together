"""Combine the three reviewed council name-enrichment outputs."""

from pathlib import Path

import pandas as pd

# Fixed staged inputs and consolidated candidate output
PROJECT_ROOT = Path(__file__).resolve().parents[2]
BASELINE_PATH = (
    PROJECT_ROOT / "data" / "processed" / "vicmap" / "vicmap_app_ready.csv"
)
STAGED_DIR = PROJECT_ROOT / "data" / "processed" / "name_enrichment"
STAGED_PATHS = {
    "MONASH": STAGED_DIR / "vicmap_app_ready_monash_enriched.csv",
    "MELBOURNE": STAGED_DIR / "vicmap_app_ready_melbourne_enriched.csv",
    "MELTON": STAGED_DIR / "vicmap_app_ready_melton_enriched.csv",
}
OUTPUT_PATH = STAGED_DIR / "vicmap_app_ready_name_enriched.csv"

NAME_COLUMNS = ["display_name", "place_name", "name_source"]
EXPECTED_TOTAL = 3237
EXPECTED_UPDATES = {
    "MONASH": 491,
    "MELBOURNE": 8,
    "MELTON": 18,
}
EXPECTED_GENERATED_RETAINED = 186


def load_csv(path):
    """Load one complete UTF-8 application dataset."""

    if not path.exists():
        raise FileNotFoundError(f"Required input not found: {path}")
    return pd.read_csv(path, encoding="utf-8-sig")


def check_structure(baseline, staged, label):
    """Confirm that one staged file retains the baseline structure."""

    if len(baseline) != len(staged) or len(staged) != EXPECTED_TOTAL:
        raise ValueError(f"Unexpected row count in {label} staged output.")
    if list(baseline.columns) != list(staged.columns):
        raise ValueError(f"Column structure changed in {label} staged output.")
    if not staged["place_id"].is_unique:
        raise ValueError(f"Duplicate place IDs in {label} staged output.")
    if set(baseline["place_id"]) != set(staged["place_id"]):
        raise ValueError(f"Place IDs changed in {label} staged output.")


def extract_updates(baseline, staged, council):
    """Extract only the reviewed name changes from one council file."""

    check_structure(baseline, staged, council)

    baseline_indexed = baseline.set_index("place_id").sort_index()
    staged_indexed = staged.set_index("place_id").sort_index()
    stable_columns = [
        column
        for column in baseline.columns
        if column not in {"place_id", *NAME_COLUMNS}
    ]

    if not baseline_indexed[stable_columns].equals(
        staged_indexed[stable_columns]
    ):
        raise ValueError(f"Non-name fields changed in {council} staged output.")

    changed_mask = baseline_indexed[NAME_COLUMNS].ne(
        staged_indexed[NAME_COLUMNS]
    ).any(axis=1)
    updates = staged_indexed.loc[changed_mask, NAME_COLUMNS].reset_index()

    if len(updates) != EXPECTED_UPDATES[council]:
        raise ValueError(
            f"Expected {EXPECTED_UPDATES[council]} {council} updates, "
            f"got {len(updates)}."
        )

    updated_lgas = staged_indexed.loc[changed_mask, "lga_name"]
    if not updated_lgas.eq(council).all():
        raise ValueError(f"{council} staged output changed another council.")

    return updates


def consolidate(baseline, staged_outputs):
    """Apply all non-overlapping reviewed name changes to the baseline."""

    all_updates = [
        extract_updates(baseline, staged_outputs[council], council)
        for council in STAGED_PATHS
    ]
    updates = pd.concat(all_updates, ignore_index=True)

    if updates["place_id"].duplicated().any():
        duplicates = updates.loc[
            updates["place_id"].duplicated(keep=False), "place_id"
        ].unique()
        raise ValueError(f"Council updates overlap: {sorted(duplicates)}")

    renamed_updates = updates.rename(
        columns={column: f"enriched_{column}" for column in NAME_COLUMNS}
    )
    consolidated = baseline.merge(
        renamed_updates,
        on="place_id",
        how="left",
        validate="one_to_one",
    )
    update_mask = consolidated["enriched_display_name"].notna()

    for column in NAME_COLUMNS:
        consolidated.loc[update_mask, column] = consolidated.loc[
            update_mask, f"enriched_{column}"
        ]

    consolidated = consolidated[baseline.columns].copy()
    expected_updated = sum(EXPECTED_UPDATES.values())

    if int(update_mask.sum()) != expected_updated:
        raise ValueError("Not every reviewed name was applied exactly once.")
    if (
        consolidated["name_source"].eq("generated_from_subtype").sum()
        != EXPECTED_GENERATED_RETAINED
    ):
        raise ValueError("Unexpected number of retained generated names.")

    return consolidated


def main():
    """Create the complete consolidated name-enriched candidate."""

    baseline = load_csv(BASELINE_PATH)
    staged_outputs = {
        council: load_csv(path)
        for council, path in STAGED_PATHS.items()
    }
    consolidated = consolidate(baseline, staged_outputs)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    consolidated.to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")

    print("Consolidated file saved:", OUTPUT_PATH)
    print("Monash names included:", EXPECTED_UPDATES["MONASH"])
    print("Melbourne names included:", EXPECTED_UPDATES["MELBOURNE"])
    print("Melton names included:", EXPECTED_UPDATES["MELTON"])
    print("Total names updated:", sum(EXPECTED_UPDATES.values()))
    print("Generated names retained:", EXPECTED_GENERATED_RETAINED)
    print("Total output records:", len(consolidated))


if __name__ == "__main__":
    main()
