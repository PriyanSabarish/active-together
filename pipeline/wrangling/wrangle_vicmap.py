"""Create the product-facing Vicmap location dataset.

This script uses Vicmap as the source of truth. It applies simple, repeatable
rules and does not use external websites or record-by-record corrections.
"""

from datetime import datetime
from pathlib import Path

import geopandas as gpd
import pandas as pd

# Project paths
PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_ROOT / "data" / "raw" / "vicmap"
RULES_PATH = (
    PROJECT_ROOT / "data" / "validation" / "vicmap" / "vicmap_subtype_review.csv"
)
BOUNDARY_PATH = (
    PROJECT_ROOT / "data" / "raw" / "boundaries" / "vicmap_lga_2026-08-26.geojson"
)
OUTPUT_PATH = PROJECT_ROOT / "data" / "processed" / "vicmap" / "vicmap_app_ready.csv"


# Product rules
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

RAW_COLUMNS = {
    "feature_id",
    "feature_type",
    "feature_subtype",
    "name",
    "name_label",
    "x_coord",
    "y_coord",
}

OUTPUT_COLUMNS = [
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


def find_latest_snapshot():
    """Return the newest complete Vicmap snapshot."""

    snapshots = []

    for path in RAW_DIR.glob("foi_index_centroid_full_*.geojson"):
        date_text = path.stem.replace("foi_index_centroid_full_", "")

        try:
            snapshot_date = datetime.strptime(date_text, "%Y-%m-%d")
        except ValueError:
            continue

        snapshots.append((snapshot_date, path))

    if not snapshots:
        raise FileNotFoundError(f"No complete Vicmap snapshot found in {RAW_DIR}")

    return max(snapshots, key=lambda item: item[0])[1]


def load_inputs():
    """Load Vicmap places, category rules and council boundaries."""

    snapshot_path = find_latest_snapshot()

    for path in [snapshot_path, RULES_PATH, BOUNDARY_PATH]:
        if not path.exists():
            raise FileNotFoundError(f"Required file not found: {path}")

    places = gpd.read_file(snapshot_path)
    rules = pd.read_csv(RULES_PATH, encoding="utf-8-sig")
    boundaries = gpd.read_file(BOUNDARY_PATH)

    print(f"Raw snapshot: {snapshot_path.name}")
    print(f"Raw records: {len(places):,}")

    return places, rules, boundaries


def check_input_columns(places, rules, boundaries):
    """Check that the input files contain the fields used below."""

    missing_raw = RAW_COLUMNS - set(places.columns)
    missing_rules = {
        "feature_type",
        "feature_subtype",
        "decision",
        "activity_category",
        "confidence_basis",
    } - set(rules.columns)
    missing_boundaries = {"lga_name", "geometry"} - set(boundaries.columns)

    if missing_raw:
        raise ValueError(f"Missing Vicmap columns: {sorted(missing_raw)}")
    if missing_rules:
        raise ValueError(f"Missing rule columns: {sorted(missing_rules)}")
    if missing_boundaries:
        raise ValueError(f"Missing boundary columns: {sorted(missing_boundaries)}")
    if places.crs is None or boundaries.crs is None:
        raise ValueError("Both spatial files must have a coordinate system.")


def clean_text(series):
    """Remove extra spaces and convert blank text to missing values."""

    return series.astype("string").str.strip().replace("", pd.NA)


def prepare_places(places):
    """Keep records with a usable ID, subtype and coordinates."""

    places = places[list(RAW_COLUMNS)].copy()

    places["feature_type"] = clean_text(places["feature_type"]).str.lower()
    places["feature_subtype"] = clean_text(places["feature_subtype"]).str.lower()
    places["name"] = clean_text(places["name"])
    places["name_label"] = clean_text(places["name_label"])

    places["feature_id"] = pd.to_numeric(places["feature_id"], errors="coerce")
    places["longitude"] = pd.to_numeric(places["x_coord"], errors="coerce")
    places["latitude"] = pd.to_numeric(places["y_coord"], errors="coerce")

    # Prefer the readable Vicmap label, then use the source name.
    places["place_name"] = places["name_label"].fillna(places["name"])
    places["name_source"] = pd.Series(pd.NA, index=places.index, dtype="string")
    places.loc[places["name"].notna(), "name_source"] = "vicmap_name"
    places.loc[places["name_label"].notna(), "name_source"] = "vicmap_name_label"

    valid_records = (
        places["feature_id"].notna()
        & places["longitude"].between(-180, 180)
        & places["latitude"].between(-90, 90)
        & places["feature_type"].notna()
        & places["feature_subtype"].notna()
    )

    removed_count = int((~valid_records).sum())
    places = places.loc[valid_records].copy()

    places["source_record_id"] = places["feature_id"].astype("int64").astype("string")
    places["place_id"] = "vicmap_foi_" + places["source_record_id"]
    places["source_dataset"] = "vicmap_foi"

    print(f"Records removed for missing required data: {removed_count:,}")

    return places


def prepare_rules(rules):
    """Keep only approved subtype-to-category mappings."""

    rules = rules[
        [
            "feature_type",
            "feature_subtype",
            "decision",
            "activity_category",
            "confidence_basis",
        ]
    ].copy()

    for column in ["feature_type", "feature_subtype", "decision"]:
        rules[column] = clean_text(rules[column]).str.lower()

    rules["activity_category"] = clean_text(rules["activity_category"]).str.lower()

    if rules.duplicated(["feature_type", "feature_subtype"]).any():
        raise ValueError("Duplicate subtype rules were found.")

    rules = rules[rules["decision"] == "include"].copy()

    invalid_categories = set(rules["activity_category"].dropna()) - ALLOWED_CATEGORIES
    if invalid_categories:
        raise ValueError(f"Invalid activity categories: {sorted(invalid_categories)}")

    rules["classification_confidence"] = (
        clean_text(rules["confidence_basis"])
        .str.lower()
        .str.extract(r"^(high|medium|low)", expand=False)
        .fillna("unresolved")
    )

    return rules.drop(columns="confidence_basis")


def apply_category_rules(places, rules):
    """Keep places whose subtype has an approved activity category."""

    classified = places.merge(
        rules,
        on=["feature_type", "feature_subtype"],
        how="inner",
        validate="many_to_one",
    )

    classified["decision"] = "include"
    print(f"Records with an approved category: {len(classified):,}")

    return classified


def assign_council(places, boundaries):
    """Assign councils and keep the three product areas."""

    boundaries = boundaries[["lga_name", "geometry"]].copy()
    boundaries["lga_name"] = clean_text(boundaries["lga_name"]).str.upper()
    boundaries = boundaries[boundaries["lga_name"].isin(PRODUCT_COUNCILS)]
    boundaries = boundaries.to_crs("EPSG:4326")

    found_councils = set(boundaries["lga_name"])
    if found_councils != PRODUCT_COUNCILS:
        missing = PRODUCT_COUNCILS - found_councils
        raise ValueError(f"Product council boundaries not found: {sorted(missing)}")

    points = gpd.GeoDataFrame(
        places,
        geometry=gpd.points_from_xy(places["longitude"], places["latitude"]),
        crs="EPSG:4326",
    )

    scoped = gpd.sjoin(
        points,
        boundaries,
        how="inner",
        predicate="within",
    )

    if scoped["place_id"].duplicated().any():
        raise ValueError("The council join created duplicate place IDs.")

    print(f"Records in Melbourne, Melton and Monash: {len(scoped):,}")

    return pd.DataFrame(scoped.drop(columns=["geometry", "index_right"]))


def remove_coordinate_duplicates(records):
    """Keep one record for each subtype at the same coordinates."""

    records = records.copy()
    records["has_source_name"] = records["place_name"].notna()
    records = records.sort_values(
        [
            "has_source_name",
            "feature_subtype",
            "longitude",
            "latitude",
            "source_record_id",
        ],
        ascending=[False, True, True, True, True],
    )

    duplicate_columns = ["feature_subtype", "longitude", "latitude"]
    duplicate_count = int(records.duplicated(duplicate_columns).sum())
    records = records.drop_duplicates(duplicate_columns, keep="first")
    records = records.drop(columns="has_source_name")

    print(f"Coordinate-subtype duplicates removed: {duplicate_count:,}")
    return records


def generate_missing_names(records):
    """Create deterministic labels for unnamed Vicmap places."""

    records = records.copy()
    missing_name = records["place_name"].isna()

    generated_names = (
        "Unnamed "
        + records.loc[missing_name, "feature_subtype"].str.title()
        + " - "
        + records.loc[missing_name, "lga_name"].str.title()
        + " - "
        + records.loc[missing_name, "source_record_id"]
    )

    records.loc[missing_name, "place_name"] = generated_names
    records.loc[missing_name, "name_source"] = "generated_from_subtype"
    records["display_name"] = records["place_name"]

    print(f"Generated names for unnamed records: {int(missing_name.sum()):,}")
    return records


def build_output(records):
    """Select the stable fields supplied to the application."""

    output = records[OUTPUT_COLUMNS].copy()
    output = output.sort_values(
        ["lga_name", "activity_category", "display_name", "place_id"]
    ).reset_index(drop=True)

    if output.empty:
        raise ValueError("The app-ready output contains no records.")
    if output["place_id"].duplicated().any():
        raise ValueError("The app-ready output contains duplicate place IDs.")
    if output[OUTPUT_COLUMNS].isna().any().any():
        raise ValueError("The app-ready output contains missing required values.")
    if set(output["activity_category"]) - ALLOWED_CATEGORIES:
        raise ValueError("The app-ready output contains an invalid category.")
    if set(output["lga_name"]) != PRODUCT_COUNCILS:
        raise ValueError("The app-ready output does not contain all product councils.")

    return output


def save_output(output):
    """Write the application CSV and print a short summary."""

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    output.to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")

    print(f"Saved {len(output):,} records to {OUTPUT_PATH}")
    print("\nRecords by council:")
    print(output["lga_name"].value_counts().sort_index().to_string())
    print("\nRecords by category:")
    print(output["activity_category"].value_counts().sort_index().to_string())


def main():
    """Run the simplified Vicmap wrangling process."""

    places, rules, boundaries = load_inputs()
    check_input_columns(places, rules, boundaries)

    places = prepare_places(places)
    rules = prepare_rules(rules)
    places = apply_category_rules(places, rules)
    places = assign_council(places, boundaries)
    places = remove_coordinate_duplicates(places)
    places = generate_missing_names(places)

    output = build_output(places)
    save_output(output)


if __name__ == "__main__":
    main()
