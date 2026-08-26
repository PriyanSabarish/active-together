"""Load and validate the Vicmap wrangling inputs."""

# 1. Imports
from pathlib import Path
import json

import geopandas as gpd
import pandas as pd

# 2. Project paths
# Resolve project paths from this script location
PROJECT_ROOT = Path(__file__).resolve().parents[2]

RAW_DATA_PATH = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "vicmap"
    / "foi_index_centroid_full_2026-08-26.geojson"
)

SUBTYPE_REVIEW_PATH = (
    PROJECT_ROOT / "data" / "validation" / "vicmap" / "vicmap_subtype_review.csv"
)

LGA_BOUNDARY_PATH = (
    PROJECT_ROOT / "data" / "raw" / "boundaries" / "vicmap_lga_2026-08-26.geojson"
)

PROCESSED_VICMAP_DIR = PROJECT_ROOT / "data" / "processed" / "vicmap"

AUDIT_OUTPUT_PATH = PROCESSED_VICMAP_DIR / "vicmap_places_greater_melbourne.csv"

RECOMMENDABLE_OUTPUT_PATH = (
    PROCESSED_VICMAP_DIR / "vicmap_recommendable_greater_melbourne.csv"
)

FALLBACK_OUTPUT_PATH = PROCESSED_VICMAP_DIR / "vicmap_fallback_greater_melbourne.csv"

PRODUCT_APP_READY_OUTPUT_PATH = PROCESSED_VICMAP_DIR / "vicmap_app_ready.csv"

PRODUCT_FALLBACK_OUTPUT_PATH = PROCESSED_VICMAP_DIR / "vicmap_fallback.csv"

# Define the duplicate-review output path
DUPLICATE_REVIEW_PATH = (
    PROJECT_ROOT / "data" / "validation" / "vicmap" / "vicmap_potential_duplicates.csv"
)

# Define the resolved product-level review rules
PRODUCT_REVIEW_PATH = (
    PROJECT_ROOT / "data" / "validation" / "vicmap" / "vicmap_product_review.csv"
)


# 3. Classification constants
# Define valid classification values
ALLOWED_DECISIONS = {
    "include",
    "exclude",
    "fallback",
    "review",
}

ALLOWED_ACTIVITY_CATEGORIES = {
    "playground",
    "park_and_garden",
    "sports_ground",
    "court",
    "trail_access",
    "skate_bmx",
    "picnic_day_use",
}

# Define the 31 councils retained as the reusable Greater Melbourne dataset
GREATER_MELBOURNE_LGAS = {
    "BANYULE",
    "BAYSIDE",
    "BOROONDARA",
    "BRIMBANK",
    "CARDINIA",
    "CASEY",
    "DAREBIN",
    "FRANKSTON",
    "GLEN EIRA",
    "GREATER DANDENONG",
    "HOBSONS BAY",
    "HUME",
    "KINGSTON",
    "KNOX",
    "MANNINGHAM",
    "MARIBYRNONG",
    "MAROONDAH",
    "MELBOURNE",
    "MELTON",
    "MERRI-BEK",
    "MONASH",
    "MOONEE VALLEY",
    "MORNINGTON PENINSULA",
    "NILLUMBIK",
    "PORT PHILLIP",
    "STONNINGTON",
    "WHITEHORSE",
    "WHITTLESEA",
    "WYNDHAM",
    "YARRA",
    "YARRA RANGES",
}

# Define the councils included in the current product scope
PRODUCT_LGAS = {
    "MELBOURNE",
    "MELTON",
    "MONASH",
}


# 4. Input functions
def load_inputs():
    """Load the raw places, subtype rules, boundaries and product review."""

    # Confirm that all required input files exist
    for input_path in [
        RAW_DATA_PATH,
        SUBTYPE_REVIEW_PATH,
        LGA_BOUNDARY_PATH,
        PRODUCT_REVIEW_PATH,
    ]:
        if not input_path.exists():
            raise FileNotFoundError(f"Required input file not found: {input_path}")

    # Load the complete raw GeoJSON snapshot
    with RAW_DATA_PATH.open(
        mode="r",
        encoding="utf-8",
    ) as file:
        geojson = json.load(file)

    # Confirm that the source is a GeoJSON FeatureCollection
    if geojson.get("type") != "FeatureCollection":
        raise ValueError("The raw Vicmap file is not a GeoJSON FeatureCollection.")

    features = geojson.get("features", [])

    if not features:
        raise ValueError("The raw Vicmap GeoJSON contains no features.")

    # Convert feature properties into a pandas DataFrame
    raw_records = pd.DataFrame(feature.get("properties", {}) for feature in features)

    # Load the subtype-level classification table
    subtype_review = pd.read_csv(
        SUBTYPE_REVIEW_PATH,
        encoding="utf-8-sig",
    )

    # Load the official Vicmap LGA polygon snapshot
    lga_boundaries = gpd.read_file(LGA_BOUNDARY_PATH)

    # Load resolved record-level product decisions
    product_review = pd.read_csv(
        PRODUCT_REVIEW_PATH,
        encoding="utf-8-sig",
        dtype="string",
        keep_default_na=False,
    )

    return raw_records, subtype_review, lga_boundaries, product_review


def validate_inputs(raw_records, subtype_review, lga_boundaries, product_review):
    """Validate required columns and mapping uniqueness."""

    # Define fields required from the Vicmap source
    required_raw_columns = {
        "feature_id",
        "feature_type",
        "feature_subtype",
        "name",
        "name_label",
        "state",
        "x_coord",
        "y_coord",
    }

    # Define fields required from the subtype review table
    required_review_columns = {
        "feature_type",
        "feature_subtype",
        "decision",
        "activity_category",
        "confidence_basis",
        "notes",
    }

    # Define fields required from the LGA boundary snapshot
    required_boundary_columns = {
        "lga_name",
        "geometry",
    }

    # Define fields required from the resolved product review table
    required_product_review_columns = {
        "place_id",
        "review_decision",
        "corrected_display_name",
        "corrected_activity_category",
        "source_url",
        "review_notes",
        "checked_date",
    }

    # Identify any missing source columns
    missing_raw_columns = required_raw_columns - set(raw_records.columns)

    if missing_raw_columns:
        raise ValueError("Missing raw data columns: " f"{sorted(missing_raw_columns)}")

    # Identify any missing review-table columns
    missing_review_columns = required_review_columns - set(subtype_review.columns)

    if missing_review_columns:
        raise ValueError(
            "Missing subtype review columns: " f"{sorted(missing_review_columns)}"
        )

    # Identify any missing boundary columns
    missing_boundary_columns = required_boundary_columns - set(lga_boundaries.columns)

    if missing_boundary_columns:
        raise ValueError(
            "Missing LGA boundary columns: " f"{sorted(missing_boundary_columns)}"
        )

    missing_product_review_columns = required_product_review_columns - set(
        product_review.columns
    )

    if missing_product_review_columns:
        raise ValueError(
            "Missing product-review columns: "
            f"{sorted(missing_product_review_columns)}"
        )

    if product_review["place_id"].duplicated().any():
        raise ValueError("Duplicate place IDs found in the product review table.")

    allowed_product_review_decisions = {
        "keep",
        "keep_preferred",
        "move_to_fallback",
        "remove_duplicate",
        "exclude",
    }

    invalid_product_review_decisions = product_review[
        ~product_review["review_decision"].isin(allowed_product_review_decisions)
    ]

    if not invalid_product_review_decisions.empty:
        raise ValueError("Unexpected decisions found in the product review table.")

    corrected_categories = product_review["corrected_activity_category"].replace(
        "", pd.NA
    )
    invalid_corrected_categories = corrected_categories[
        ~corrected_categories.isin(ALLOWED_ACTIVITY_CATEGORIES)
        & corrected_categories.notna()
    ]

    if not invalid_corrected_categories.empty:
        raise ValueError("Invalid corrected activity categories found in product review.")

    if product_review["source_url"].eq("").any():
        raise ValueError("Every product review decision must include a source URL.")

    if lga_boundaries.crs is None:
        raise ValueError("The LGA boundary snapshot has no coordinate system.")

    # Confirm that every configured metro council exists in the snapshot
    boundary_names = set(
        lga_boundaries["lga_name"].astype("string").str.strip().str.upper().dropna()
    )

    missing_metro_lgas = GREATER_MELBOURNE_LGAS - boundary_names

    if missing_metro_lgas:
        raise ValueError(
            "Configured Greater Melbourne LGAs are missing from "
            f"the boundary snapshot: {sorted(missing_metro_lgas)}"
        )

    # Confirm that each type-subtype mapping is unique
    duplicate_rules = subtype_review.duplicated(
        subset=["feature_type", "feature_subtype"],
        keep=False,
    )

    if duplicate_rules.any():
        raise ValueError("Duplicate type-subtype rules found in the review table.")

    # Report the successfully loaded inputs
    print(f"Raw records loaded: {len(raw_records):,}")
    print(f"Raw columns loaded: {len(raw_records.columns)}")
    print(f"Subtype rules loaded: {len(subtype_review):,}")
    print(f"LGA boundaries loaded: {len(lga_boundaries):,}")
    print(f"Product review decisions loaded: {len(product_review):,}")
    print("Input validation completed successfully.")


# 5. Base-record functions
def prepare_base_records(raw_records):
    """Create a standardised base table from the raw Vicmap records."""

    # Select only the fields needed by the application pipeline
    base_records = raw_records[
        [
            "feature_id",
            "feature_type",
            "feature_subtype",
            "name",
            "name_label",
            "state",
            "x_coord",
            "y_coord",
        ]
    ].copy()

    # Standardise category text for reliable rule matching
    for column in ["feature_type", "feature_subtype"]:
        base_records[column] = (
            base_records[column].astype("string").str.strip().str.lower()
        )

    # Standardise both source name fields before selecting a name
    name_labels = (
        base_records["name_label"].astype("string").str.strip().replace("", pd.NA)
    )

    source_names = base_records["name"].astype("string").str.strip().replace("", pd.NA)

    # Prefer the readable label and fall back to the source name
    base_records["place_name"] = name_labels.combine_first(source_names)

    # Record which Vicmap field supplied the retained place name
    base_records["name_source"] = pd.Series(
        pd.NA,
        index=base_records.index,
        dtype="string",
    )

    base_records.loc[
        name_labels.notna(),
        "name_source",
    ] = "vicmap_name_label"

    base_records.loc[
        name_labels.isna() & source_names.notna(),
        "name_source",
    ] = "vicmap_name"

    # Convert source coordinates to numeric values
    base_records["longitude"] = pd.to_numeric(
        base_records["x_coord"],
        errors="coerce",
    )

    base_records["latitude"] = pd.to_numeric(
        base_records["y_coord"],
        errors="coerce",
    )

    # Create a source-qualified ID for later dataset integration
    base_records["source_record_id"] = (
        base_records["feature_id"].astype("Int64").astype("string")
    )

    base_records["place_id"] = "vicmap_foi_" + base_records["source_record_id"]

    # Record the source dataset for every place
    base_records["source_dataset"] = "vicmap_foi"

    # Keep only the standardised pipeline columns
    base_records = base_records[
        [
            "place_id",
            "source_record_id",
            "source_dataset",
            "place_name",
            "name_source",
            "feature_type",
            "feature_subtype",
            "state",
            "longitude",
            "latitude",
        ]
    ]

    return base_records


def validate_base_records(base_records):
    """Validate IDs, coordinates and basic record quality."""

    # Confirm that every generated place ID is unique
    duplicate_place_ids = base_records["place_id"].duplicated().sum()

    if duplicate_place_ids:
        raise ValueError(f"Duplicate place IDs found: {duplicate_place_ids}")

    # Confirm that every record has usable coordinates
    missing_coordinates = (
        base_records[["longitude", "latitude"]].isna().any(axis=1).sum()
    )

    if missing_coordinates:
        raise ValueError(f"Records with missing coordinates: {missing_coordinates}")

    # Confirm that coordinates are valid longitude and latitude values
    invalid_coordinates = ~base_records["longitude"].between(-180, 180) | ~base_records[
        "latitude"
    ].between(-90, 90)

    if invalid_coordinates.any():
        raise ValueError("Coordinates outside valid WGS84 bounds were found.")

    # Report name completeness without removing unnamed places
    missing_names = base_records["place_name"].isna().sum()
    missing_name_percent = missing_names / len(base_records) * 100

    print(f"Standardised records: {len(base_records):,}")
    print(f"Duplicate place IDs: {duplicate_place_ids:,}")
    print(f"Missing coordinates: {missing_coordinates:,}")
    print(f"Missing place names: {missing_names:,} " f"({missing_name_percent:.2f}%)")
    print("Base-record validation completed successfully.")


# 6. Geographic scope functions
def filter_greater_melbourne(base_records, lga_boundaries):
    """Keep records located within the configured metro councils."""

    # Standardise boundary names for matching against the council list
    boundaries = lga_boundaries[["lga_name", "geometry"]].copy()

    boundaries["lga_name"] = (
        boundaries["lga_name"].astype("string").str.strip().str.upper()
    )

    # Select only the 31 metropolitan Melbourne council polygons
    metro_boundaries = boundaries[
        boundaries["lga_name"].isin(GREATER_MELBOURNE_LGAS)
    ].copy()

    if len(metro_boundaries) != len(GREATER_MELBOURNE_LGAS):
        raise ValueError(
            "The metro boundary selection did not return "
            "exactly one polygon record per configured LGA."
        )

    # Reproject the boundary layer to match the FOI coordinates
    metro_boundaries = metro_boundaries.to_crs("EPSG:4326")

    # Create point geometries from the standardised coordinates
    place_points = gpd.GeoDataFrame(
        base_records.copy(),
        geometry=gpd.points_from_xy(
            base_records["longitude"],
            base_records["latitude"],
        ),
        crs="EPSG:4326",
    )

    # Attach the containing council and remove statewide records
    scoped_records = gpd.sjoin(
        place_points,
        metro_boundaries[["lga_name", "geometry"]],
        how="inner",
        predicate="within",
    )

    # Confirm that the spatial join did not duplicate source records
    duplicate_place_ids = scoped_records["place_id"].duplicated().sum()

    if duplicate_place_ids:
        raise ValueError(
            "The LGA spatial join created duplicate place IDs: "
            f"{duplicate_place_ids:,}"
        )

    # Return a regular DataFrame without spatial helper columns
    scoped_records = pd.DataFrame(
        scoped_records.drop(
            columns=["geometry", "index_right"],
        )
    ).reset_index(drop=True)

    matched_lgas = scoped_records["lga_name"].nunique()

    print(
        "Greater Melbourne records retained: "
        f"{len(scoped_records):,} of {len(base_records):,}"
    )
    print(
        "Metropolitan councils represented: "
        f"{matched_lgas:,} of {len(GREATER_MELBOURNE_LGAS):,}"
    )
    print("Greater Melbourne filtering completed successfully.")

    return scoped_records


# 7. Classification functions
def prepare_subtype_rules(subtype_review):
    """Prepare and validate subtype classification rules."""

    # Keep only fields required during classification
    rules = subtype_review[
        [
            "feature_type",
            "feature_subtype",
            "decision",
            "activity_category",
            "confidence_basis",
            "notes",
        ]
    ].copy()

    # Standardise rule keys to match the base records
    for column in ["feature_type", "feature_subtype", "decision"]:
        rules[column] = rules[column].astype("string").str.strip().str.lower()

    # Standardise activity category values while preserving missing values
    rules["activity_category"] = (
        rules["activity_category"].astype("string").str.strip().str.lower()
    )

    # Confirm that every decision is permitted
    invalid_decisions = rules[~rules["decision"].isin(ALLOWED_DECISIONS)]

    if not invalid_decisions.empty:
        raise ValueError("Unexpected decision values found in subtype rules.")

    # Confirm that included rules use one of the seven categories
    invalid_included_categories = rules[
        (rules["decision"] == "include")
        & (~rules["activity_category"].isin(ALLOWED_ACTIVITY_CATEGORIES))
    ]

    if not invalid_included_categories.empty:
        raise ValueError("An included subtype has an invalid activity category.")

    # Confirm that non-included rules do not have an activity category
    unexpected_categories = rules[
        (rules["decision"] != "include") & (rules["activity_category"].notna())
    ]

    if not unexpected_categories.empty:
        raise ValueError("A non-included subtype has an activity category.")

    return rules


def apply_subtype_rules(base_records, subtype_review):
    """Join subtype classification rules to every place record."""

    # Prepare the validated subtype mapping
    rules = prepare_subtype_rules(subtype_review)

    # Join each place to exactly one subtype rule
    classified_records = base_records.merge(
        rules,
        on=["feature_type", "feature_subtype"],
        how="left",
        validate="many_to_one",
        indicator=True,
    )

    # Identify any raw records without a matching subtype rule
    unmatched_records = classified_records[classified_records["_merge"] != "both"]

    if not unmatched_records.empty:
        unmatched_subtypes = unmatched_records[
            ["feature_type", "feature_subtype"]
        ].drop_duplicates()

        raise ValueError(
            "Records without subtype rules were found:\n"
            f"{unmatched_subtypes.to_string(index=False)}"
        )

    # Remove the temporary merge indicator
    classified_records = classified_records.drop(columns="_merge")

    # Create application-facing eligibility flags
    classified_records["is_recommendable"] = classified_records["decision"] == "include"

    classified_records["is_fallback"] = classified_records["decision"] == "fallback"

    # Extract a concise confidence level from the evidence text
    classified_records["classification_confidence"] = (
        classified_records["confidence_basis"]
        .astype("string")
        .str.extract(
            r"^(high|medium|low)",
            expand=False,
        )
        .fillna("unresolved")
    )

    return classified_records


def validate_classified_records(
    classified_records,
    expected_record_count,
):
    """Validate record coverage after applying subtype rules."""

    # Confirm that classification preserved the scoped record count
    if len(classified_records) != expected_record_count:
        raise ValueError(
            "Record count changed during classification. "
            f"Expected {expected_record_count:,}, "
            f"received {len(classified_records):,}."
        )

    # Confirm that every scoped record received a decision
    missing_decisions = classified_records["decision"].isna().sum()

    if missing_decisions:
        raise ValueError(f"Records without a decision: {missing_decisions}")

    # Summarise the classification outcome
    decision_counts = (
        classified_records["decision"]
        .value_counts()
        .reindex(
            ["include", "exclude", "fallback", "review"],
            fill_value=0,
        )
    )

    print("Record-level classification:")
    print(decision_counts.to_string())
    print("Classification merge completed successfully.")


# 8. Recommendation profiling functions
def profile_recommendable_records(classified_records):
    """Profile names and potential duplicates in included records."""

    # Select records eligible for ranked recommendations
    recommendable_records = classified_records[
        classified_records["is_recommendable"]
    ].copy()

    # Measure missing place names among included records
    missing_names = recommendable_records["place_name"].isna().sum()

    missing_name_percent = missing_names / len(recommendable_records) * 100

    # Find records that share exactly the same coordinates
    duplicate_coordinate_rows = recommendable_records.duplicated(
        subset=["longitude", "latitude"],
        keep=False,
    )

    # Find records sharing both coordinates and subtype
    duplicate_subtype_rows = recommendable_records.duplicated(
        subset=[
            "longitude",
            "latitude",
            "feature_subtype",
        ],
        keep=False,
    )

    # Count coordinate groups rather than only affected rows
    duplicate_coordinate_groups = (
        recommendable_records.groupby(["longitude", "latitude"]).size().gt(1).sum()
    )

    duplicate_subtype_groups = (
        recommendable_records.groupby(
            [
                "longitude",
                "latitude",
                "feature_subtype",
            ]
        )
        .size()
        .gt(1)
        .sum()
    )

    print("Recommendable-record profile:")
    print(f"Included records: " f"{len(recommendable_records):,}")
    print(
        f"Missing place names: " f"{missing_names:,} " f"({missing_name_percent:.2f}%)"
    )
    print(f"Rows sharing coordinates: " f"{duplicate_coordinate_rows.sum():,}")
    print(f"Duplicate coordinate groups: " f"{duplicate_coordinate_groups:,}")
    print(f"Rows sharing coordinates and subtype: " f"{duplicate_subtype_rows.sum():,}")
    print(f"Duplicate coordinate-subtype groups: " f"{duplicate_subtype_groups:,}")


# 9. Duplicate-review export functions
def export_duplicate_review(classified_records):
    """Export potential duplicate records for manual review."""

    group_columns = [
        "longitude",
        "latitude",
        "feature_subtype",
    ]

    # Select records eligible for ranked recommendations
    recommendable_records = classified_records[
        classified_records["is_recommendable"]
    ].copy()

    # Count records sharing coordinates and subtype
    recommendable_records["duplicate_group_size"] = recommendable_records.groupby(
        group_columns
    )["place_id"].transform("size")

    # Keep only groups containing more than one record
    duplicate_review = recommendable_records[
        recommendable_records["duplicate_group_size"] > 1
    ].copy()

    # Sort groups so the generated review IDs are reproducible
    duplicate_review = duplicate_review.sort_values(
        [
            "longitude",
            "latitude",
            "feature_subtype",
            "place_name",
        ],
        na_position="last",
    ).reset_index(drop=True)

    # Assign one concise ID to each coordinate-subtype group
    group_numbers = (
        duplicate_review.groupby(
            group_columns,
            sort=False,
            dropna=False,
        ).ngroup()
        + 1
    )

    duplicate_review["duplicate_group_id"] = group_numbers.map(
        lambda value: f"vicmap_dup_{value:03d}"
    )

    # Normalise names only for generating non-binding suggestions
    duplicate_review["_normalised_name"] = (
        duplicate_review["place_name"]
        .astype("string")
        .str.strip()
        .replace("", pd.NA)
        .str.casefold()
    )

    distinct_name_counts = duplicate_review.groupby(
        group_columns,
        dropna=False,
    )[
        "_normalised_name"
    ].transform("nunique")

    # Suggest an action without applying any deletion rule
    duplicate_review["suggested_action"] = "review"
    duplicate_review.loc[
        distinct_name_counts == 1,
        "suggested_action",
    ] = "keep_preferred"
    duplicate_review.loc[
        distinct_name_counts > 1,
        "suggested_action",
    ] = "keep_all"

    # Leave final review fields blank for a human decision
    duplicate_review["review_decision"] = ""
    duplicate_review["keep_record"] = ""
    duplicate_review["review_notes"] = ""
    duplicate_review["review_source"] = ""

    # Select fields useful for grouped manual comparison
    duplicate_review = duplicate_review[
        [
            "duplicate_group_id",
            "lga_name",
            "longitude",
            "latitude",
            "feature_type",
            "feature_subtype",
            "duplicate_group_size",
            "place_id",
            "source_record_id",
            "place_name",
            "activity_category",
            "suggested_action",
            "review_decision",
            "keep_record",
            "review_notes",
            "review_source",
        ]
    ]

    # Preserve completed review fields when the export is regenerated
    manual_columns = [
        "review_decision",
        "keep_record",
        "review_notes",
        "review_source",
    ]

    if DUPLICATE_REVIEW_PATH.exists():
        previous_review = pd.read_csv(
            DUPLICATE_REVIEW_PATH,
            encoding="utf-8-sig",
            dtype="string",
            keep_default_na=False,
        )

        available_manual_columns = [
            column for column in manual_columns if column in previous_review.columns
        ]

        if "place_id" in previous_review.columns and available_manual_columns:
            previous_review = previous_review[
                ["place_id", *available_manual_columns]
            ].drop_duplicates(
                subset="place_id",
                keep="last",
            )

            duplicate_review = duplicate_review.merge(
                previous_review,
                on="place_id",
                how="left",
                validate="one_to_one",
                suffixes=("", "_previous"),
            )

            for column in available_manual_columns:
                previous_column = f"{column}_previous"
                has_previous_value = duplicate_review[previous_column].fillna("").ne("")

                duplicate_review.loc[
                    has_previous_value,
                    column,
                ] = duplicate_review.loc[
                    has_previous_value,
                    previous_column,
                ]

                duplicate_review = duplicate_review.drop(columns=previous_column)

    # Ensure that the validation output directory exists
    DUPLICATE_REVIEW_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    # Save candidates without changing the classified records
    duplicate_review.to_csv(
        DUPLICATE_REVIEW_PATH,
        index=False,
        encoding="utf-8-sig",
    )

    print(f"Potential duplicate rows exported: " f"{len(duplicate_review):,}")
    print(f"Duplicate review file: " f"{DUPLICATE_REVIEW_PATH}")

    return duplicate_review


# 10. Reviewed duplicate application functions
def validate_duplicate_review(
    duplicate_review,
    classified_records,
):
    """Validate completed duplicate decisions before applying them."""

    # Define fields required from the completed review table
    required_columns = {
        "duplicate_group_id",
        "place_id",
        "review_decision",
        "keep_record",
    }

    missing_columns = required_columns - set(duplicate_review.columns)

    if missing_columns:
        raise ValueError(
            "Missing duplicate-review columns: " f"{sorted(missing_columns)}"
        )

    # Confirm that each candidate place appears only once
    if duplicate_review["place_id"].duplicated().any():
        raise ValueError("Duplicate place IDs were found in the review table.")

    # Confirm that all reviewed IDs exist in the classified data
    unknown_place_ids = set(duplicate_review["place_id"]) - set(
        classified_records["place_id"]
    )

    if unknown_place_ids:
        raise ValueError("The duplicate review contains unknown place IDs.")

    # Require all groups to have a final actionable decision
    allowed_review_decisions = {
        "keep_all",
        "keep_preferred",
    }

    invalid_decisions = duplicate_review[
        ~duplicate_review["review_decision"].isin(allowed_review_decisions)
    ]

    if not invalid_decisions.empty:
        raise ValueError("Unresolved or invalid duplicate decisions remain.")

    # Require an explicit yes or no for every candidate record
    invalid_keep_values = duplicate_review[
        ~duplicate_review["keep_record"].isin({"yes", "no"})
    ]

    if not invalid_keep_values.empty:
        raise ValueError("Every duplicate candidate must have keep_record yes or no.")

    # Confirm that each group uses one consistent review decision
    inconsistent_groups = (
        duplicate_review.groupby("duplicate_group_id")["review_decision"]
        .nunique()
        .gt(1)
    )

    if inconsistent_groups.any():
        raise ValueError("A duplicate group contains inconsistent decisions.")

    # Confirm that keep-all groups retain every record
    invalid_keep_all_groups = (
        duplicate_review[duplicate_review["review_decision"] == "keep_all"]
        .groupby("duplicate_group_id")["keep_record"]
        .apply(lambda values: not values.eq("yes").all())
    )

    if invalid_keep_all_groups.any():
        raise ValueError("A keep_all group contains a record marked no.")

    # Confirm that preferred groups retain exactly one record
    preferred_groups = duplicate_review[
        duplicate_review["review_decision"] == "keep_preferred"
    ]

    preferred_keep_counts = (
        preferred_groups.assign(_keep_yes=preferred_groups["keep_record"].eq("yes"))
        .groupby("duplicate_group_id")["_keep_yes"]
        .sum()
    )

    if preferred_keep_counts.ne(1).any():
        raise ValueError("A keep_preferred group does not retain exactly one record.")

    print(
        "Completed duplicate groups validated: "
        f"{duplicate_review['duplicate_group_id'].nunique():,}"
    )
    print("Duplicate-review validation completed successfully.")


def apply_duplicate_review(
    classified_records,
    duplicate_review,
):
    """Remove only records explicitly rejected during review."""

    # Join row-level keep decisions back to the classified records
    review_actions = duplicate_review[["place_id", "keep_record"]].copy()

    reviewed_records = classified_records.merge(
        review_actions,
        on="place_id",
        how="left",
        validate="one_to_one",
    )

    # Identify records explicitly rejected as duplicate candidates
    remove_mask = reviewed_records["keep_record"].eq("no")

    if (
        ~reviewed_records.loc[
            remove_mask,
            "is_recommendable",
        ]
    ).any():
        raise ValueError("A non-recommendable record was marked for duplicate removal.")

    removed_count = int(remove_mask.sum())

    # Keep all unreviewed rows and reviewed rows marked yes
    deduplicated_records = (
        reviewed_records.loc[~remove_mask]
        .drop(columns="keep_record")
        .reset_index(drop=True)
    )

    if deduplicated_records["place_id"].duplicated().any():
        raise ValueError("Duplicate place IDs remain after applying the review.")

    recommendable_count = int(deduplicated_records["is_recommendable"].sum())

    print(f"Reviewed duplicate records removed: {removed_count:,}")
    print(
        "Recommendable records after reviewed deduplication: "
        f"{recommendable_count:,}"
    )
    print("Reviewed deduplication completed successfully.")

    return deduplicated_records


def validate_deduplicated_records(
    deduplicated_records,
    duplicate_review,
):
    """Validate the scoped records after reviewed deduplication."""

    # Confirm that every retained place ID remains unique
    duplicate_place_ids = deduplicated_records["place_id"].duplicated().sum()

    if duplicate_place_ids:
        raise ValueError("Duplicate place IDs remain after deduplication.")

    # Confirm that all rejected candidate IDs were removed
    rejected_place_ids = set(
        duplicate_review.loc[
            duplicate_review["keep_record"] == "no",
            "place_id",
        ]
    )

    retained_rejected_ids = rejected_place_ids & set(deduplicated_records["place_id"])

    if retained_rejected_ids:
        raise ValueError("A rejected duplicate candidate remains in the data.")

    # Confirm that recommendable records use the seven valid categories
    recommendable_records = deduplicated_records[
        deduplicated_records["is_recommendable"]
    ].copy()

    invalid_categories = recommendable_records[
        ~recommendable_records["activity_category"].isin(ALLOWED_ACTIVITY_CATEGORIES)
    ]

    if not invalid_categories.empty:
        raise ValueError("A recommendable record has an invalid activity category.")

    # Identify remaining coordinate-subtype groups after review
    remaining_duplicate_mask = recommendable_records.duplicated(
        subset=[
            "longitude",
            "latitude",
            "feature_subtype",
        ],
        keep=False,
    )

    remaining_duplicate_records = recommendable_records[remaining_duplicate_mask]

    remaining_duplicate_ids = set(remaining_duplicate_records["place_id"])

    approved_keep_all_ids = set(
        duplicate_review.loc[
            (duplicate_review["review_decision"] == "keep_all")
            & (duplicate_review["keep_record"] == "yes"),
            "place_id",
        ]
    )

    if remaining_duplicate_ids != approved_keep_all_ids:
        raise ValueError(
            "Remaining coordinate-subtype duplicates do not match "
            "the approved keep_all groups."
        )

    remaining_duplicate_groups = remaining_duplicate_records.groupby(
        [
            "longitude",
            "latitude",
            "feature_subtype",
        ]
    ).ngroups

    # Summarise final classification and name completeness
    decision_counts = (
        deduplicated_records["decision"]
        .value_counts()
        .reindex(
            ["include", "exclude", "fallback", "review"],
            fill_value=0,
        )
    )

    missing_recommendable_names = recommendable_records["place_name"].isna().sum()

    missing_name_percent = (
        missing_recommendable_names / len(recommendable_records) * 100
    )

    print("Final scoped classification:")
    print(decision_counts.to_string())
    print("Final Greater Melbourne records: " f"{len(deduplicated_records):,}")
    print("Final recommendable records: " f"{len(recommendable_records):,}")
    print(
        "Missing recommendable names: "
        f"{missing_recommendable_names:,} "
        f"({missing_name_percent:.2f}%)"
    )
    print(
        "Approved keep_all duplicate groups retained: "
        f"{remaining_duplicate_groups:,}"
    )
    print("Final deduplicated validation completed successfully.")


# 11. Display-name functions
def prepare_display_names(deduplicated_records):
    """Create application-facing names without replacing source names."""

    processed_records = deduplicated_records.copy()

    # Build a readable fallback from subtype and council context
    fallback_type = (
        processed_records["feature_subtype"]
        .astype("string")
        .str.replace("_", " ", regex=False)
        .str.title()
    )

    fallback_council = processed_records["lga_name"].astype("string").str.title()

    fallback_names = "Unnamed " + fallback_type + " - " + fallback_council

    # Use the official source name wherever one is available
    processed_records["display_name"] = processed_records["place_name"].combine_first(
        fallback_names
    )

    # Mark generated labels so they are never treated as official names
    generated_name_mask = processed_records["place_name"].isna()

    processed_records.loc[
        generated_name_mask,
        "name_source",
    ] = "generated_fallback"

    return processed_records


def validate_display_names(processed_records):
    """Validate application-facing names and their provenance."""

    # Confirm that every retained record has a usable display name
    missing_display_names = processed_records["display_name"].isna().sum()

    blank_display_names = (
        processed_records["display_name"].astype("string").str.strip().eq("").sum()
    )

    if missing_display_names or blank_display_names:
        raise ValueError("Missing or blank application display names were found.")

    # Confirm that every name uses an approved provenance value
    allowed_name_sources = {
        "vicmap_name_label",
        "vicmap_name",
        "generated_fallback",
    }

    invalid_name_sources = processed_records[
        ~processed_records["name_source"].isin(allowed_name_sources)
    ]

    if not invalid_name_sources.empty:
        raise ValueError("Unexpected name provenance values were found.")

    # Confirm that generated labels are used only for missing source names
    invalid_generated_names = processed_records[
        (processed_records["name_source"] == "generated_fallback")
        & processed_records["place_name"].notna()
    ]

    if not invalid_generated_names.empty:
        raise ValueError("A generated fallback replaced an available source name.")

    name_source_counts = (
        processed_records["name_source"]
        .value_counts()
        .reindex(
            [
                "vicmap_name_label",
                "vicmap_name",
                "generated_fallback",
            ],
            fill_value=0,
        )
    )

    generated_recommendable_names = (
        processed_records["is_recommendable"]
        & (processed_records["name_source"] == "generated_fallback")
    ).sum()

    print("Display-name provenance:")
    print(name_source_counts.to_string())
    print(
        "Generated fallback names in recommendable records: "
        f"{generated_recommendable_names:,}"
    )
    print("Display-name validation completed successfully.")


# 12. Processed-data export functions
def filter_product_scope(processed_records):
    """Select and validate records for the current product councils."""

    # Ensure every product council belongs to the retained master scope
    invalid_product_lgas = PRODUCT_LGAS - GREATER_MELBOURNE_LGAS

    if invalid_product_lgas:
        raise ValueError(
            "Product LGAs are outside the Greater Melbourne scope: "
            f"{sorted(invalid_product_lgas)}"
        )

    # Select the configured councils without changing the master dataset
    product_records = processed_records[
        processed_records["lga_name"].isin(PRODUCT_LGAS)
    ].copy()

    represented_lgas = set(product_records["lga_name"].dropna().unique())
    missing_product_lgas = PRODUCT_LGAS - represented_lgas

    if missing_product_lgas:
        raise ValueError(
            "No processed records were found for product LGAs: "
            f"{sorted(missing_product_lgas)}"
        )

    print(
        "Product councils represented: "
        f"{len(represented_lgas):,} of {len(PRODUCT_LGAS):,}"
    )
    print(f"Product-scope records retained: {len(product_records):,}")

    return product_records


def apply_product_review(product_records, product_review):
    """Apply resolved record-level decisions only to product-scope outputs."""

    reviewed_records = product_records.copy()
    review_rules = product_review.copy()

    # Normalise harmless source-name formatting for product display
    reviewed_records["display_name"] = (
        reviewed_records["display_name"]
        .astype("string")
        .str.replace(r"\s+", " ", regex=True)
        .str.replace(r"\bPavillion\b", "Pavilion", case=False, regex=True)
        .str.strip()
    )

    # Treat named club sport facilities as managed-access fallback places
    club_sport_facility_mask = (
        reviewed_records["is_recommendable"]
        & reviewed_records["feature_type"].eq("sport facility")
        & reviewed_records["display_name"].str.contains(
            r"\bclub\b",
            case=False,
            regex=True,
            na=False,
        )
    )
    club_fallback_count = int(club_sport_facility_mask.sum())
    reviewed_records.loc[club_sport_facility_mask, "decision"] = "fallback"
    reviewed_records.loc[club_sport_facility_mask, "is_recommendable"] = False
    reviewed_records.loc[club_sport_facility_mask, "is_fallback"] = True

    print(
        "Club sport facilities moved to fallback by policy: "
        f"{club_fallback_count:,}"
    )

    # Remove linear transport-landscape records that are not activity destinations
    linear_non_destination_mask = (
        reviewed_records["activity_category"].eq("park_and_garden")
        & reviewed_records["display_name"].str.contains(
            r"\b(?:walkway|streetscape|navigation drive)\b",
            case=False,
            regex=True,
            na=False,
        )
    )
    linear_removed_count = int(linear_non_destination_mask.sum())
    reviewed_records = reviewed_records.loc[~linear_non_destination_mask].copy()

    print(
        "Linear non-destination records removed by policy: "
        f"{linear_removed_count:,}"
    )

    # Collapse only clear same-location duplicates not covered by manual review
    manually_reviewed_ids = set(review_rules["place_id"])
    duplicate_pool = reviewed_records[
        reviewed_records["is_recommendable"]
        & ~reviewed_records["place_id"].isin(manually_reviewed_ids)
    ].copy()
    duplicate_pool["_rounded_longitude"] = duplicate_pool["longitude"].round(6)
    duplicate_pool["_rounded_latitude"] = duplicate_pool["latitude"].round(6)

    automatic_duplicate_removals = set()
    duplicate_group_columns = [
        "lga_name",
        "_rounded_longitude",
        "_rounded_latitude",
        "activity_category",
    ]

    for _, group in duplicate_pool.groupby(duplicate_group_columns, sort=False):
        if len(group) < 2:
            continue

        normalised_names = (
            group["display_name"]
            .astype("string")
            .str.casefold()
            .str.replace(r"\s+", " ", regex=True)
            .str.strip()
        )
        location_bases = normalised_names.str.split(" - ", n=1).str[0]
        names = normalised_names.tolist()
        one_name_contains_another = any(
            first in second or second in first
            for index, first in enumerate(names)
            for second in names[index + 1 :]
        )

        if location_bases.nunique() != 1 and not one_name_contains_another:
            continue

        preferred_record = (
            group.assign(_display_length=normalised_names.str.len())
            .sort_values(
                ["_display_length", "place_id"],
                ascending=[False, True],
                kind="stable",
            )
            .iloc[0]
        )
        automatic_duplicate_removals.update(
            set(group["place_id"]) - {preferred_record["place_id"]}
        )

    reviewed_records = reviewed_records[
        ~reviewed_records["place_id"].isin(automatic_duplicate_removals)
    ].copy()

    print(
        "Clear same-location duplicates removed by policy: "
        f"{len(automatic_duplicate_removals):,}"
    )

    # Standardise rule values while preserving intentionally blank corrections
    for column in [
        "place_id",
        "review_decision",
        "corrected_display_name",
        "corrected_activity_category",
    ]:
        review_rules[column] = review_rules[column].astype("string").str.strip()

    product_place_ids = set(reviewed_records["place_id"])
    configured_place_ids = set(review_rules["place_id"])
    stale_place_ids = configured_place_ids - product_place_ids

    # Stale IDs may occur after a future API refresh and should remain auditable
    if stale_place_ids:
        print(
            "Product review decisions not present in this source snapshot: "
            f"{len(stale_place_ids):,}"
        )

    applicable_rules = review_rules[
        review_rules["place_id"].isin(product_place_ids)
    ].copy()

    if applicable_rules.empty:
        raise ValueError("No product review decisions match the product-scope records.")

    reviewed_records = reviewed_records.merge(
        applicable_rules[
            [
                "place_id",
                "review_decision",
                "corrected_display_name",
                "corrected_activity_category",
            ]
        ],
        on="place_id",
        how="left",
        validate="one_to_one",
    )

    reviewed_mask = reviewed_records["review_decision"].notna()
    corrected_name_mask = reviewed_mask & reviewed_records[
        "corrected_display_name"
    ].ne("")
    corrected_category_mask = reviewed_mask & reviewed_records[
        "corrected_activity_category"
    ].ne("")

    # Apply reviewed display-name and category corrections
    reviewed_records.loc[
        corrected_name_mask,
        "display_name",
    ] = reviewed_records.loc[corrected_name_mask, "corrected_display_name"]
    reviewed_records.loc[
        corrected_name_mask,
        "name_source",
    ] = "reviewed_override"
    reviewed_records.loc[
        corrected_category_mask,
        "activity_category",
    ] = reviewed_records.loc[
        corrected_category_mask,
        "corrected_activity_category",
    ]

    # Convert reviewed access-risk records from app-ready to fallback
    fallback_mask = reviewed_records["review_decision"].eq("move_to_fallback")
    reviewed_records.loc[fallback_mask, "decision"] = "fallback"
    reviewed_records.loc[fallback_mask, "is_recommendable"] = False
    reviewed_records.loc[fallback_mask, "is_fallback"] = True

    # Keep reviewed public destinations in the main recommendation pool
    keep_mask = reviewed_records["review_decision"].isin(
        {"keep", "keep_preferred"}
    )
    reviewed_records.loc[keep_mask, "decision"] = "include"
    reviewed_records.loc[keep_mask, "is_recommendable"] = True
    reviewed_records.loc[keep_mask, "is_fallback"] = False

    # Remove unsuitable places and rejected duplicate rows from product outputs
    remove_mask = reviewed_records["review_decision"].isin(
        {"exclude", "remove_duplicate"}
    )
    removed_count = int(remove_mask.sum())
    reviewed_records = reviewed_records.loc[~remove_mask].copy()

    reviewed_records = reviewed_records.drop(
        columns=[
            "review_decision",
            "corrected_display_name",
            "corrected_activity_category",
        ]
    ).reset_index(drop=True)

    if reviewed_records["place_id"].duplicated().any():
        raise ValueError("Duplicate place IDs remain after product review.")

    # Confirm every applicable rule produced its intended final state
    retained_ids = set(reviewed_records["place_id"])
    expected_removed_ids = set(
        applicable_rules.loc[
            applicable_rules["review_decision"].isin(
                {"exclude", "remove_duplicate"}
            ),
            "place_id",
        ]
    )

    if expected_removed_ids & retained_ids:
        raise ValueError("A product record marked for removal was retained.")

    fallback_ids = set(
        reviewed_records.loc[reviewed_records["is_fallback"], "place_id"]
    )
    expected_fallback_ids = set(
        applicable_rules.loc[
            applicable_rules["review_decision"].eq("move_to_fallback"),
            "place_id",
        ]
    )

    if not expected_fallback_ids.issubset(fallback_ids):
        raise ValueError("A reviewed fallback record was not moved to fallback.")

    decision_summary = applicable_rules["review_decision"].value_counts()

    print("Applied product review decisions:")
    print(decision_summary.to_string())
    print(f"Product records removed by review: {removed_count:,}")
    print(f"Product records retained after review: {len(reviewed_records):,}")
    print("Product review application completed successfully.")

    return reviewed_records


def export_processed_data(processed_records, product_review):
    """Export Greater Melbourne master and product-facing outputs."""

    # Create the dataset-specific processed output directory
    PROCESSED_VICMAP_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    # Keep all scoped decisions for reproducibility and auditing
    audit_records = processed_records.copy()

    # Select records eligible for the main recommendation pool
    recommendable_records = processed_records[
        processed_records["is_recommendable"]
    ].copy()

    # Select records reserved for explicit fallback behaviour
    fallback_records = processed_records[processed_records["is_fallback"]].copy()

    # Create the product subset after completing the master processing steps
    product_records = filter_product_scope(processed_records)

    # Apply manually resolved decisions without changing the master dataset
    product_records = apply_product_review(
        product_records,
        product_review,
    )

    # Select the main recommendation pool for the product
    product_app_ready_records = product_records[
        product_records["is_recommendable"]
    ].copy()

    # Select uncertain records reserved for product fallback behaviour
    product_fallback_records = product_records[product_records["is_fallback"]].copy()

    # Define a stable application-facing column order
    application_columns = [
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

    recommendable_records = recommendable_records[application_columns]

    fallback_records = fallback_records[application_columns]

    product_app_ready_records = product_app_ready_records[application_columns]

    product_fallback_records = product_fallback_records[application_columns]

    # Write Excel-friendly UTF-8 CSV outputs
    audit_records.to_csv(
        AUDIT_OUTPUT_PATH,
        index=False,
        encoding="utf-8-sig",
    )

    recommendable_records.to_csv(
        RECOMMENDABLE_OUTPUT_PATH,
        index=False,
        encoding="utf-8-sig",
    )

    fallback_records.to_csv(
        FALLBACK_OUTPUT_PATH,
        index=False,
        encoding="utf-8-sig",
    )

    product_app_ready_records.to_csv(
        PRODUCT_APP_READY_OUTPUT_PATH,
        index=False,
        encoding="utf-8-sig",
    )

    product_fallback_records.to_csv(
        PRODUCT_FALLBACK_OUTPUT_PATH,
        index=False,
        encoding="utf-8-sig",
    )

    return {
        AUDIT_OUTPUT_PATH: len(audit_records),
        RECOMMENDABLE_OUTPUT_PATH: len(recommendable_records),
        FALLBACK_OUTPUT_PATH: len(fallback_records),
        PRODUCT_APP_READY_OUTPUT_PATH: len(product_app_ready_records),
        PRODUCT_FALLBACK_OUTPUT_PATH: len(product_fallback_records),
    }


def validate_processed_exports(expected_outputs):
    """Reload and validate every processed CSV output."""

    for output_path, expected_count in expected_outputs.items():
        if not output_path.exists():
            raise FileNotFoundError(f"Processed output was not created: {output_path}")

        exported_records = pd.read_csv(
            output_path,
            encoding="utf-8-sig",
        )

        if len(exported_records) != expected_count:
            raise ValueError(
                "Processed output row count changed after writing: "
                f"{output_path.name}"
            )

        if exported_records["place_id"].duplicated().any():
            raise ValueError(
                "Duplicate place IDs were found in processed output: "
                f"{output_path.name}"
            )

        print(
            f"Processed output validated: {output_path.name} "
            f"({expected_count:,} rows)"
        )

    print("Processed-data export completed successfully.")


# 13. Pipeline entry point
def main():
    """Run the Vicmap wrangling pipeline."""

    # Load and validate the places, rules and boundary snapshot
    raw_records, subtype_review, lga_boundaries, product_review = load_inputs()
    validate_inputs(
        raw_records,
        subtype_review,
        lga_boundaries,
        product_review,
    )

    # Create and validate the statewide base table
    base_records = prepare_base_records(raw_records)
    validate_base_records(base_records)

    # Restrict all later processing to Greater Melbourne
    scoped_records = filter_greater_melbourne(
        base_records,
        lga_boundaries,
    )

    # Apply the reusable subtype rules to the scoped data
    classified_records = apply_subtype_rules(
        scoped_records,
        subtype_review,
    )

    validate_classified_records(
        classified_records,
        expected_record_count=len(scoped_records),
    )

    # Profile included records within the Greater Melbourne scope
    profile_recommendable_records(classified_records)

    # Export scoped duplicate candidates for manual review
    duplicate_review = export_duplicate_review(classified_records)

    # Validate and apply the completed manual review
    validate_duplicate_review(
        duplicate_review,
        classified_records,
    )

    deduplicated_records = apply_duplicate_review(
        classified_records,
        duplicate_review,
    )

    # Run final quality checks before processed-data export
    validate_deduplicated_records(
        deduplicated_records,
        duplicate_review,
    )

    # Create and validate application-facing display names
    processed_records = prepare_display_names(deduplicated_records)

    validate_display_names(processed_records)

    # Export and reload all processed pipeline outputs
    expected_outputs = export_processed_data(
        processed_records,
        product_review,
    )

    validate_processed_exports(expected_outputs)


if __name__ == "__main__":
    main()
