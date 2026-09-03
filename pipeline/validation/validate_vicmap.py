"""Validate the Vicmap CSV used by the application.

"""

from pathlib import Path

import geopandas as gpd
import pandas as pd


# Project files
PROJECT_ROOT = Path(__file__).resolve().parents[2]
APP_READY_PATH = (
    PROJECT_ROOT / "data" / "processed" / "vicmap" / "vicmap_app_ready.csv"
)
BOUNDARY_PATH = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "boundaries"
    / "vicmap_lga_2026-08-26.geojson"
)


# Expected product scope
PRODUCT_COUNCILS = {"MELBOURNE", "MELTON", "MONASH"}

ALLOWED_CATEGORIES = {
    "playground",
    "park_and_garden",
    "sports_ground",
    "court",
    "trail_access",
    "skate_bmx",
    "picnic_day_use",
}

ALLOWED_NAME_SOURCES = {
    "vicmap_name",
    "vicmap_name_label",
    "generated_from_subtype",
}

REQUIRED_COLUMNS = [
    "place_id",
    "display_name",
    "place_name",
    "name_source",
    "activity_category",
    "classification_confidence",
    "lga_name",
    "longitude",
    "latitude",
    "feature_type",
    "feature_subtype",
    "decision",
    "source_dataset",
    "source_record_id",
]

TEXT_COLUMNS = [
    "place_id",
    "display_name",
    "place_name",
    "name_source",
    "activity_category",
    "classification_confidence",
    "lga_name",
    "feature_type",
    "feature_subtype",
    "decision",
    "source_dataset",
    "source_record_id",
]


def load_inputs():
    """Load the app-ready CSV and LGA boundaries."""

    for path in [APP_READY_PATH, BOUNDARY_PATH]:
        if not path.exists():
            raise FileNotFoundError(f"Required file not found: {path}")

    records = pd.read_csv(APP_READY_PATH, encoding="utf-8-sig")
    boundaries = gpd.read_file(BOUNDARY_PATH)

    print(f"App-ready records loaded: {len(records):,}")
    return records, boundaries


def validate_structure(records):
    """Check columns, missing values and unique identifiers."""

    if records.empty:
        raise ValueError("The app-ready CSV contains no records.")

    missing_columns = set(REQUIRED_COLUMNS) - set(records.columns)
    extra_columns = set(records.columns) - set(REQUIRED_COLUMNS)

    if missing_columns:
        raise ValueError(f"Missing columns: {sorted(missing_columns)}")
    if extra_columns:
        raise ValueError(f"Unexpected columns: {sorted(extra_columns)}")

    # Blank text is treated as missing data.
    blank_values = records[TEXT_COLUMNS].apply(
        lambda column: column.astype("string").str.strip().eq("")
    )

    if records[REQUIRED_COLUMNS].isna().any().any() or blank_values.any().any():
        raise ValueError("The app-ready CSV contains missing required values.")

    if records["place_id"].duplicated().any():
        raise ValueError("The app-ready CSV contains duplicate place IDs.")

    print("Table structure passed.")


def validate_coordinates(records):
    """Check that longitude and latitude are valid numbers."""

    longitude = pd.to_numeric(records["longitude"], errors="coerce")
    latitude = pd.to_numeric(records["latitude"], errors="coerce")

    if longitude.isna().any() or latitude.isna().any():
        raise ValueError("Some coordinates are missing or non-numeric.")
    if not longitude.between(-180, 180).all():
        raise ValueError("Some longitude values are outside the valid range.")
    if not latitude.between(-90, 90).all():
        raise ValueError("Some latitude values are outside the valid range.")

    print("Coordinate values passed.")


def validate_product_rules(records):
    """Check councils, categories and fixed source values."""

    councils = set(records["lga_name"])
    categories = set(records["activity_category"])

    if councils != PRODUCT_COUNCILS:
        raise ValueError(
            "Council coverage does not match the product scope. "
            f"Found: {sorted(councils)}"
        )

    invalid_categories = categories - ALLOWED_CATEGORIES
    if invalid_categories:
        raise ValueError(f"Invalid categories: {sorted(invalid_categories)}")

    missing_categories = ALLOWED_CATEGORIES - categories
    if missing_categories:
        raise ValueError(f"Categories with no records: {sorted(missing_categories)}")

    if not records["decision"].eq("include").all():
        raise ValueError("Every app-ready record must have decision='include'.")

    if not records["source_dataset"].eq("vicmap_foi").all():
        raise ValueError("Every record must identify Vicmap FOI as its source.")

    invalid_name_sources = set(records["name_source"]) - ALLOWED_NAME_SOURCES
    if invalid_name_sources:
        raise ValueError(f"Invalid name sources: {sorted(invalid_name_sources)}")

    generated = records["name_source"].eq("generated_from_subtype")
    expected_names = (
        "Unnamed "
        + records.loc[generated, "feature_subtype"].astype("string").str.title()
        + " - "
        + records.loc[generated, "lga_name"].astype("string").str.title()
        + " - "
        + records.loc[generated, "source_record_id"].astype("string")
    )

    if not records.loc[generated, "display_name"].astype("string").eq(
        expected_names
    ).all():
        raise ValueError("One or more generated names do not follow the rule.")

    duplicate_columns = ["feature_subtype", "longitude", "latitude"]
    if records.duplicated(duplicate_columns).any():
        raise ValueError("Duplicate coordinate-subtype records were found.")

    print("Product rules passed.")


def validate_spatial_scope(records, boundaries):
    """Confirm that each point falls inside its stated council."""

    required_boundary_columns = {"lga_name", "geometry"}
    missing_columns = required_boundary_columns - set(boundaries.columns)

    if missing_columns:
        raise ValueError(f"Boundary file is missing: {sorted(missing_columns)}")
    if boundaries.crs is None:
        raise ValueError("The boundary file has no coordinate system.")

    boundaries = boundaries[["lga_name", "geometry"]].copy()
    boundaries["lga_name"] = boundaries["lga_name"].astype("string").str.upper()
    boundaries = boundaries[boundaries["lga_name"].isin(PRODUCT_COUNCILS)]
    boundaries = boundaries.to_crs("EPSG:4326")

    if set(boundaries["lga_name"]) != PRODUCT_COUNCILS:
        raise ValueError("One or more product council boundaries are missing.")

    points = gpd.GeoDataFrame(
        records.copy(),
        geometry=gpd.points_from_xy(records["longitude"], records["latitude"]),
        crs="EPSG:4326",
    )

    # Check each declared council against its own boundary.
    for council in sorted(PRODUCT_COUNCILS):
        council_area = boundaries.loc[
            boundaries["lga_name"] == council, "geometry"
        ].union_all()
        council_points = points.loc[points["lga_name"] == council, "geometry"]
        outside_count = int((~council_points.apply(council_area.covers)).sum())

        if outside_count:
            raise ValueError(
                f"{outside_count:,} {council} records fall outside its boundary."
            )

    print("Spatial scope passed.")


def print_summary(records):
    """Print small summaries for a human review."""

    print("\nRecords by council:")
    print(records["lga_name"].value_counts().sort_index().to_string())

    print("\nRecords by category:")
    print(records["activity_category"].value_counts().sort_index().to_string())


def main():
    """Run all validation checks."""

    records, boundaries = load_inputs()
    validate_structure(records)
    validate_coordinates(records)
    validate_product_rules(records)
    validate_spatial_scope(records, boundaries)
    print_summary(records)

    print("\nVicmap validation completed successfully.")


if __name__ == "__main__":
    main()
