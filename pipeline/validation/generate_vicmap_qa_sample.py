"""Create a reproducible QA sample from the app-ready Vicmap dataset.

The sample supports manual classification checks. It does not change the
app-ready CSV or make record-level corrections.
"""

from pathlib import Path

import pandas as pd


# Project files
PROJECT_ROOT = Path(__file__).resolve().parents[2]
APP_READY_PATH = (
    PROJECT_ROOT / "data" / "processed" / "vicmap" / "vicmap_app_ready.csv"
)
OUTPUT_PATH = (
    PROJECT_ROOT / "data" / "validation" / "vicmap" / "vicmap_qa_sample.csv"
)


# Sampling rules
SAMPLE_PER_CATEGORY = 30
RANDOM_SEED = 5120

ALLOWED_CATEGORIES = {
    "playground",
    "park_and_garden",
    "sports_ground",
    "court",
    "trail_access",
    "skate_bmx",
    "picnic_day_use",
}

SOURCE_COLUMNS = [
    "place_id",
    "display_name",
    "name_source",
    "activity_category",
    "lga_name",
    "longitude",
    "latitude",
    "feature_type",
    "feature_subtype",
    "source_record_id",
]

REVIEW_COLUMNS = [
    "reviewer_1_result",
    "reviewer_1_suggested_category",
    "reviewer_1_notes",
    "reviewer_2_result",
    "reviewer_2_suggested_category",
    "reviewer_2_notes",
    "final_result",
    "final_category",
    "resolution_notes",
]


def load_app_ready_data():
    """Load the validated application CSV."""

    if not APP_READY_PATH.exists():
        raise FileNotFoundError(f"App-ready CSV not found: {APP_READY_PATH}")

    records = pd.read_csv(APP_READY_PATH, encoding="utf-8-sig")
    missing_columns = set(SOURCE_COLUMNS) - set(records.columns)

    if records.empty:
        raise ValueError("The app-ready CSV contains no records.")
    if missing_columns:
        raise ValueError(f"Missing columns: {sorted(missing_columns)}")
    if records["place_id"].duplicated().any():
        raise ValueError("The app-ready CSV contains duplicate place IDs.")

    categories = set(records["activity_category"])

    if categories != ALLOWED_CATEGORIES:
        raise ValueError(
            "Activity categories do not match the expected product categories."
        )

    print(f"App-ready records loaded: {len(records):,}")
    return records


def create_sample(records):
    """Select up to 30 reproducible records from each category."""

    samples = []

    for category in sorted(ALLOWED_CATEGORIES):
        category_records = records[
            records["activity_category"] == category
        ].sort_values("place_id")

        sample_size = min(SAMPLE_PER_CATEGORY, len(category_records))
        category_sample = category_records.sample(
            n=sample_size,
            random_state=RANDOM_SEED,
        )
        samples.append(category_sample)

        print(
            f"{category}: sampled {sample_size:,} "
            f"of {len(category_records):,} records"
        )

    sample = pd.concat(samples, ignore_index=True)
    sample = sample[SOURCE_COLUMNS].sort_values(
        ["activity_category", "lga_name", "display_name", "place_id"]
    )
    sample = sample.reset_index(drop=True)
    sample.insert(0, "sample_id", range(1, len(sample) + 1))

    # Empty columns are completed independently by two reviewers.
    for column in REVIEW_COLUMNS:
        sample[column] = ""

    return sample


def save_sample(sample):
    """Save the QA table without overwriting an existing review."""

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    if OUTPUT_PATH.exists():
        raise FileExistsError(
            f"QA sample already exists and will not be overwritten: {OUTPUT_PATH}"
        )

    sample.to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")

    print(f"QA sample saved: {OUTPUT_PATH}")
    print(f"QA sample records: {len(sample):,}")


def main():
    """Generate the Vicmap classification QA sample."""

    records = load_app_ready_data()
    sample = create_sample(records)
    save_sample(sample)


if __name__ == "__main__":
    main()
