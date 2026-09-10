"""Validate and optionally publish the consolidated name-enriched dataset."""

import argparse
import shutil
from pathlib import Path

import pandas as pd

# Fixed baseline, staged evidence and publication paths
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
CONSOLIDATED_PATH = STAGED_DIR / "vicmap_app_ready_name_enriched.csv"
PUBLISHED_PATH = PROJECT_ROOT / "data" / "vicmap_app_ready.csv"

NAME_COLUMNS = ["display_name", "place_name", "name_source"]
EXPECTED_TOTAL = 3237
EXPECTED_UPDATES = {
    "MONASH": 491,
    "MELBOURNE": 8,
    "MELTON": 18,
}
EXPECTED_GENERATED_RETAINED = 186


def load_csv(path):
    """Load one required application CSV."""

    if not path.exists():
        raise FileNotFoundError(f"Required input not found: {path}")
    return pd.read_csv(path, encoding="utf-8-sig")


def expected_updates(baseline, staged_outputs):
    """Recreate the expected union from the three validated staged files."""

    baseline_indexed = baseline.set_index("place_id").sort_index()
    update_frames = []

    for council, staged in staged_outputs.items():
        assert len(staged) == EXPECTED_TOTAL
        assert list(staged.columns) == list(baseline.columns)
        assert staged["place_id"].is_unique
        assert set(staged["place_id"]) == set(baseline["place_id"])

        staged_indexed = staged.set_index("place_id").sort_index()
        stable_columns = [
            column
            for column in baseline.columns
            if column not in {"place_id", *NAME_COLUMNS}
        ]
        assert baseline_indexed[stable_columns].equals(
            staged_indexed[stable_columns]
        )

        changed_mask = baseline_indexed[NAME_COLUMNS].ne(
            staged_indexed[NAME_COLUMNS]
        ).any(axis=1)
        assert int(changed_mask.sum()) == EXPECTED_UPDATES[council]
        assert staged_indexed.loc[changed_mask, "lga_name"].eq(council).all()

        update_frames.append(
            staged_indexed.loc[changed_mask, NAME_COLUMNS].reset_index()
        )

    updates = pd.concat(update_frames, ignore_index=True)
    assert not updates["place_id"].duplicated().any()
    return updates.set_index("place_id").sort_index()


def validate():
    """Validate the consolidated candidate and return its dataframe."""

    baseline = load_csv(BASELINE_PATH)
    consolidated = load_csv(CONSOLIDATED_PATH)
    staged_outputs = {
        council: load_csv(path)
        for council, path in STAGED_PATHS.items()
    }

    assert len(baseline) == len(consolidated) == EXPECTED_TOTAL
    assert baseline["place_id"].is_unique
    assert consolidated["place_id"].is_unique
    assert list(baseline.columns) == list(consolidated.columns)
    assert set(baseline["place_id"]) == set(consolidated["place_id"])

    baseline_indexed = baseline.set_index("place_id").sort_index()
    consolidated_indexed = consolidated.set_index("place_id").sort_index()
    stable_columns = [
        column
        for column in baseline.columns
        if column not in {"place_id", *NAME_COLUMNS}
    ]
    assert baseline_indexed[stable_columns].equals(
        consolidated_indexed[stable_columns]
    )

    expected = expected_updates(baseline, staged_outputs)
    changed_mask = baseline_indexed[NAME_COLUMNS].ne(
        consolidated_indexed[NAME_COLUMNS]
    ).any(axis=1)
    changed = consolidated_indexed.loc[changed_mask, NAME_COLUMNS]

    assert set(changed.index) == set(expected.index)
    assert changed.equals(expected)
    assert len(changed) == sum(EXPECTED_UPDATES.values())
    assert changed["display_name"].eq(changed["place_name"]).all()
    assert changed["display_name"].notna().all()
    assert changed["display_name"].eq(changed["display_name"].str.strip()).all()
    assert not changed["display_name"].str.contains(r"\s{2,}", regex=True).any()
    assert not changed["display_name"].str.lower().str.startswith("unnamed").any()

    generated_retained = consolidated["name_source"].eq(
        "generated_from_subtype"
    ).sum()
    assert generated_retained == EXPECTED_GENERATED_RETAINED

    print("Consolidated name-enrichment validation passed.")
    print(f"Monash names: {EXPECTED_UPDATES['MONASH']:,}")
    print(f"Melbourne names: {EXPECTED_UPDATES['MELBOURNE']:,}")
    print(f"Melton names: {EXPECTED_UPDATES['MELTON']:,}")
    print(f"Total names updated: {len(changed):,}")
    print(f"Generated names retained: {generated_retained:,}")
    print(f"Total output records: {len(consolidated):,}")

    return consolidated


def publish():
    """Atomically replace the application delivery CSV after validation."""

    temporary_path = PUBLISHED_PATH.with_suffix(".csv.tmp")
    shutil.copyfile(CONSOLIDATED_PATH, temporary_path)
    temporary_path.replace(PUBLISHED_PATH)
    print("Published application CSV:", PUBLISHED_PATH)


def main():
    """Validate the candidate and publish only when explicitly requested."""

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--publish",
        action="store_true",
        help="Replace data/vicmap_app_ready.csv after validation passes.",
    )
    args = parser.parse_args()

    validate()
    if args.publish:
        publish()


if __name__ == "__main__":
    main()
