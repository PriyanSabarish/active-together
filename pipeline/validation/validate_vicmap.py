"""Validate the product-facing Vicmap CSV outputs."""

# 1. Imports
from pathlib import Path

import geopandas as gpd
import pandas as pd


# 2. Project paths
# Resolve project paths from this script location
PROJECT_ROOT = Path(__file__).resolve().parents[2]

PROCESSED_VICMAP_DIR = PROJECT_ROOT / "data" / "processed" / "vicmap"
VALIDATION_VICMAP_DIR = PROJECT_ROOT / "data" / "validation" / "vicmap"

APP_READY_PATH = PROCESSED_VICMAP_DIR / "vicmap_app_ready.csv"
FALLBACK_PATH = PROCESSED_VICMAP_DIR / "vicmap_fallback.csv"

LGA_BOUNDARY_PATH = (
    PROJECT_ROOT / "data" / "raw" / "boundaries" / "vicmap_lga_2026-08-26.geojson"
)

QA_SAMPLE_PATH = VALIDATION_VICMAP_DIR / "vicmap_app_ready_qa_sample.csv"

REVIEW_CANDIDATES_PATH = (
    VALIDATION_VICMAP_DIR / "vicmap_product_review_candidates.csv"
)

PRODUCT_REVIEW_PATH = VALIDATION_VICMAP_DIR / "vicmap_product_review.csv"


# 3. Validation constants
PRODUCT_LGAS = {
    "MELBOURNE",
    "MELTON",
    "MONASH",
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

REQUIRED_COLUMNS = {
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
}

SAMPLE_PER_COUNCIL_CATEGORY = 3
RANDOM_STATE = 42

QA_REVIEW_COLUMNS = [
    "qa_status",
    "review_notes",
    "source_url",
    "checked_date",
]

MANUAL_REVIEW_COLUMNS = [
    "review_status",
    "review_decision",
    "corrected_display_name",
    "corrected_activity_category",
    "source_url",
    "review_notes",
    "checked_date",
]

GENERIC_DISPLAY_NAMES = {
    "oval",
    "park",
    "reserve",
    "playground",
    "sports ground",
    "sports complex",
    "tennis court",
    "basketball court",
    "netball court",
    "picnic area",
}

EDUCATION_ACCESS_PATTERN = (
    r"\b(?:school|college|university|academy|kindergarten|childcare)\b"
)

CLUB_ACCESS_PATTERN = r"\bclub\b"

AMBIGUOUS_DESTINATION_PATTERN = r"\bpavilion\b"


# 4. Input functions
def load_inputs():
    """Load product outputs, boundaries and resolved review decisions."""

    # Confirm that every required validation input exists
    for input_path in [
        APP_READY_PATH,
        FALLBACK_PATH,
        LGA_BOUNDARY_PATH,
        PRODUCT_REVIEW_PATH,
    ]:
        if not input_path.exists():
            raise FileNotFoundError(f"Required validation input not found: {input_path}")

    app_ready = pd.read_csv(APP_READY_PATH, encoding="utf-8-sig")
    fallback = pd.read_csv(FALLBACK_PATH, encoding="utf-8-sig")
    lga_boundaries = gpd.read_file(LGA_BOUNDARY_PATH)
    product_review = pd.read_csv(
        PRODUCT_REVIEW_PATH,
        encoding="utf-8-sig",
        dtype="string",
        keep_default_na=False,
    )

    print(f"App-ready records loaded: {len(app_ready):,}")
    print(f"Fallback records loaded: {len(fallback):,}")
    print(f"LGA boundaries loaded: {len(lga_boundaries):,}")
    print(f"Resolved product reviews loaded: {len(product_review):,}")

    return app_ready, fallback, lga_boundaries, product_review


# 5. Table validation functions
def validate_table_structure(records, table_name):
    """Validate required columns, identifiers, names and coordinates."""

    if records.empty:
        raise ValueError(f"{table_name} contains no records.")

    missing_columns = REQUIRED_COLUMNS - set(records.columns)

    if missing_columns:
        raise ValueError(
            f"{table_name} is missing required columns: {sorted(missing_columns)}"
        )

    if records["place_id"].isna().any():
        raise ValueError(f"{table_name} contains missing place IDs.")

    if records["place_id"].duplicated().any():
        raise ValueError(f"{table_name} contains duplicate place IDs.")

    empty_display_names = (
        records["display_name"].isna()
        | records["display_name"].astype("string").str.strip().eq("")
    )

    if empty_display_names.any():
        raise ValueError(f"{table_name} contains empty display names.")

    # Convert coordinates before applying numeric range checks
    longitude = pd.to_numeric(records["longitude"], errors="coerce")
    latitude = pd.to_numeric(records["latitude"], errors="coerce")

    if longitude.isna().any() or latitude.isna().any():
        raise ValueError(f"{table_name} contains missing or invalid coordinates.")

    if not longitude.between(-180, 180).all():
        raise ValueError(f"{table_name} contains invalid longitude values.")

    if not latitude.between(-90, 90).all():
        raise ValueError(f"{table_name} contains invalid latitude values.")

    invalid_lgas = set(records["lga_name"].dropna().unique()) - PRODUCT_LGAS

    if invalid_lgas:
        raise ValueError(
            f"{table_name} contains councils outside the product scope: "
            f"{sorted(invalid_lgas)}"
        )

    print(f"{table_name} structure validated successfully.")


def validate_product_rules(app_ready, fallback):
    """Validate decision rules and separation between product outputs."""

    if not app_ready["decision"].eq("include").all():
        raise ValueError("The app-ready output contains a non-include decision.")

    if not fallback["decision"].eq("fallback").all():
        raise ValueError("The fallback output contains a non-fallback decision.")

    invalid_categories = set(app_ready["activity_category"].dropna().unique()) - (
        ALLOWED_ACTIVITY_CATEGORIES
    )

    if invalid_categories:
        raise ValueError(
            "The app-ready output contains invalid activity categories: "
            f"{sorted(invalid_categories)}"
        )

    if app_ready["activity_category"].isna().any():
        raise ValueError("The app-ready output contains missing activity categories.")

    represented_lgas = set(app_ready["lga_name"].dropna().unique())
    missing_lgas = PRODUCT_LGAS - represented_lgas

    if missing_lgas:
        raise ValueError(
            "The app-ready output is missing product councils: "
            f"{sorted(missing_lgas)}"
        )

    overlapping_ids = set(app_ready["place_id"]) & set(fallback["place_id"])

    if overlapping_ids:
        raise ValueError(
            "Place IDs appear in both app-ready and fallback outputs: "
            f"{len(overlapping_ids):,}"
        )

    print("Product decision rules validated successfully.")


def validate_product_review_application(app_ready, fallback, product_review):
    """Confirm resolved product decisions are reflected in current outputs."""

    required_review_columns = {
        "place_id",
        "review_decision",
        "corrected_display_name",
        "corrected_activity_category",
        "source_url",
        "review_notes",
        "checked_date",
    }
    missing_columns = required_review_columns - set(product_review.columns)

    if missing_columns:
        raise ValueError(
            "The product review table is missing columns: "
            f"{sorted(missing_columns)}"
        )

    if product_review["place_id"].duplicated().any():
        raise ValueError("The product review table contains duplicate place IDs.")

    allowed_decisions = {
        "keep",
        "keep_preferred",
        "move_to_fallback",
        "remove_duplicate",
        "exclude",
    }
    invalid_decisions = product_review[
        ~product_review["review_decision"].isin(allowed_decisions)
    ]

    if not invalid_decisions.empty:
        raise ValueError("The product review table contains invalid decisions.")

    app_by_id = app_ready.set_index("place_id")
    fallback_by_id = fallback.set_index("place_id")
    current_ids = set(app_ready["place_id"]) | set(fallback["place_id"])

    for review in product_review.itertuples(index=False):
        decision = review.review_decision
        place_id = review.place_id

        if decision in {"exclude", "remove_duplicate"}:
            if place_id in current_ids:
                raise ValueError(
                    f"Reviewed record marked {decision} remains in product output: "
                    f"{place_id}"
                )
            continue

        # A reviewed source record may become stale after a future API refresh
        if place_id not in current_ids:
            continue

        expected_table = fallback_by_id if decision == "move_to_fallback" else app_by_id
        unexpected_table = app_by_id if decision == "move_to_fallback" else fallback_by_id

        if place_id not in expected_table.index:
            raise ValueError(
                "Reviewed record was not written to its expected product output: "
                f"{place_id}"
            )

        if place_id in unexpected_table.index:
            raise ValueError(
                "Reviewed record appears in both or in the wrong product output: "
                f"{place_id}"
            )

        exported = expected_table.loc[place_id]

        if review.corrected_display_name:
            if exported["display_name"] != review.corrected_display_name:
                raise ValueError(
                    "Reviewed display-name correction was not applied: " f"{place_id}"
                )

        if review.corrected_activity_category:
            if exported["activity_category"] != review.corrected_activity_category:
                raise ValueError(
                    "Reviewed activity-category correction was not applied: "
                    f"{place_id}"
                )

    print("Resolved product review decisions validated successfully.")


# 6. Spatial validation functions
def validate_spatial_assignment(app_ready, fallback, lga_boundaries):
    """Confirm that exported coordinates fall inside their assigned council."""

    required_boundary_columns = {"lga_name", "geometry"}
    missing_columns = required_boundary_columns - set(lga_boundaries.columns)

    if missing_columns:
        raise ValueError(
            "The LGA boundary snapshot is missing columns: "
            f"{sorted(missing_columns)}"
        )

    if lga_boundaries.crs is None:
        raise ValueError("The LGA boundary snapshot has no coordinate system.")

    # Standardise council labels and coordinates for the spatial check
    boundaries = lga_boundaries[["lga_name", "geometry"]].copy()
    boundaries["boundary_lga"] = (
        boundaries["lga_name"].astype("string").str.strip().str.upper()
    )
    boundaries = boundaries[boundaries["boundary_lga"].isin(PRODUCT_LGAS)]
    boundaries = boundaries[["boundary_lga", "geometry"]].to_crs("EPSG:4326")

    represented_boundaries = set(boundaries["boundary_lga"].dropna().unique())
    missing_boundaries = PRODUCT_LGAS - represented_boundaries

    if missing_boundaries:
        raise ValueError(
            "The boundary snapshot is missing product councils: "
            f"{sorted(missing_boundaries)}"
        )

    combined_records = pd.concat(
        [
            app_ready.assign(output_table="app_ready"),
            fallback.assign(output_table="fallback"),
        ],
        ignore_index=True,
    )

    points = gpd.GeoDataFrame(
        combined_records,
        geometry=gpd.points_from_xy(
            combined_records["longitude"],
            combined_records["latitude"],
        ),
        crs="EPSG:4326",
    )

    # Use intersects so points exactly on a council boundary can still match
    spatial_check = gpd.sjoin(
        points,
        boundaries,
        how="left",
        predicate="intersects",
    )

    if spatial_check["place_id"].duplicated().any():
        raise ValueError("The spatial validation produced multiple council matches.")

    unmatched = spatial_check["boundary_lga"].isna()

    if unmatched.any():
        raise ValueError(
            "Product coordinates outside the selected council boundaries: "
            f"{int(unmatched.sum()):,}"
        )

    mismatched = spatial_check["lga_name"] != spatial_check["boundary_lga"]

    if mismatched.any():
        raise ValueError(
            "Product coordinates assigned to the wrong council: "
            f"{int(mismatched.sum()):,}"
        )

    print("Product spatial assignments validated successfully.")


# 7. Reporting and sampling functions
def print_quality_summary(app_ready, fallback):
    """Print concise council, category and name-source summaries."""

    council_summary = (
        app_ready.groupby("lga_name")
        .agg(
            app_ready_count=("place_id", "count"),
            category_count=("activity_category", "nunique"),
            source_name_count=(
                "name_source",
                lambda values: values.ne("generated_fallback").sum(),
            ),
            generated_name_count=(
                "name_source",
                lambda values: values.eq("generated_fallback").sum(),
            ),
        )
        .sort_index()
    )

    fallback_summary = fallback.groupby("lga_name").size().rename("fallback_count")
    council_summary = council_summary.join(fallback_summary, how="left").fillna(
        {"fallback_count": 0}
    )
    council_summary["fallback_count"] = council_summary["fallback_count"].astype(int)

    category_summary = (
        app_ready.groupby(["lga_name", "activity_category"])
        .size()
        .rename("record_count")
        .unstack(fill_value=0)
        .sort_index()
    )

    print("\nCouncil quality summary:")
    print(council_summary.to_string())
    print("\nApp-ready category distribution:")
    print(category_summary.to_string())
    print("\nFallback subtype distribution:")
    print(
        fallback.groupby(["lga_name", "feature_subtype"])
        .size()
        .rename("record_count")
        .to_string()
    )


def export_review_candidates(app_ready, fallback, product_review):
    """Export all product records that trigger a defined review risk."""

    # Combine both product outputs so fallback records enter the same workflow
    review_base = pd.concat(
        [
            app_ready.assign(output_table="app_ready"),
            fallback.assign(output_table="fallback"),
        ],
        ignore_index=True,
    )

    # Do not reopen records already resolved in the formal product review table
    resolved_place_ids = set(product_review["place_id"])
    review_base = review_base[
        ~review_base["place_id"].isin(resolved_place_ids)
    ].reset_index(drop=True)

    # Create normalised helper fields used only for deterministic risk detection
    review_base["normalised_display_name"] = (
        review_base["display_name"]
        .astype("string")
        .str.replace(r"\s+", " ", regex=True)
        .str.strip()
        .str.casefold()
    )
    review_base["rounded_longitude"] = review_base["longitude"].round(6)
    review_base["rounded_latitude"] = review_base["latitude"].round(6)

    searchable_text = (
        review_base[
            [
                "display_name",
                "place_name",
                "feature_type",
                "feature_subtype",
            ]
        ]
        .fillna("")
        .astype("string")
        .agg(" ".join, axis=1)
        .str.casefold()
    )

    reasons_by_index = {index: [] for index in review_base.index}
    priority_by_index = {index: 0 for index in review_base.index}
    priority_scores = {
        "low": 1,
        "medium": 2,
        "high": 3,
    }

    def add_review_reason(mask, reason, priority):
        """Attach one reason and retain the highest triggered priority."""

        for index in review_base.index[mask]:
            reasons_by_index[index].append(reason)
            priority_by_index[index] = max(
                priority_by_index[index],
                priority_scores[priority],
            )

    app_ready_mask = review_base["output_table"].eq("app_ready")

    # Identify records that would produce duplicate recommendations in the app
    duplicate_display_keys = [
        "lga_name",
        "rounded_longitude",
        "rounded_latitude",
        "activity_category",
        "normalised_display_name",
    ]
    duplicate_display_mask = pd.Series(False, index=review_base.index)
    duplicate_display_mask.loc[app_ready_mask] = review_base.loc[
        app_ready_mask
    ].duplicated(
        subset=duplicate_display_keys,
        keep=False,
    )
    add_review_reason(
        duplicate_display_mask,
        "duplicate_display_location_category",
        "high",
    )

    # Identify nearby records in the same app category that may still duplicate a place
    coordinate_category_keys = [
        "lga_name",
        "rounded_longitude",
        "rounded_latitude",
        "activity_category",
    ]
    coordinate_category_mask = pd.Series(False, index=review_base.index)
    coordinate_category_mask.loc[app_ready_mask] = review_base.loc[
        app_ready_mask
    ].duplicated(
        subset=coordinate_category_keys,
        keep=False,
    )
    add_review_reason(
        coordinate_category_mask & ~duplicate_display_mask,
        "shared_location_and_category",
        "medium",
    )

    # Flag education-linked facilities because public access cannot be assumed
    education_access_mask = app_ready_mask & searchable_text.str.contains(
        EDUCATION_ACCESS_PATTERN,
        regex=True,
        na=False,
    )
    add_review_reason(
        education_access_mask,
        "education_or_childcare_access_risk",
        "high",
    )

    # Flag club facilities for booking, membership and fee checks
    club_access_mask = (
        app_ready_mask
        & review_base["feature_type"].eq("sport facility")
        & searchable_text.str.contains(
            CLUB_ACCESS_PATTERN,
            regex=True,
            na=False,
        )
    )
    add_review_reason(
        club_access_mask,
        "club_booking_or_fee_risk",
        "medium",
    )

    # Flag names that are too generic or poorly formatted for product display
    generic_name_mask = app_ready_mask & review_base[
        "normalised_display_name"
    ].isin(GENERIC_DISPLAY_NAMES)
    add_review_reason(
        generic_name_mask,
        "generic_display_name",
        "medium",
    )

    formatting_mask = app_ready_mask & review_base["display_name"].astype(
        "string"
    ).str.contains(
        r"\s{2,}|pavillion",
        case=False,
        regex=True,
        na=False,
    )
    add_review_reason(
        formatting_mask,
        "display_name_formatting_issue",
        "medium",
    )

    # Keep ambiguous linear features and pavilion labels visible for review
    ambiguous_destination_mask = app_ready_mask & review_base[
        "normalised_display_name"
    ].str.contains(
        AMBIGUOUS_DESTINATION_PATTERN,
        regex=True,
        na=False,
    )
    add_review_reason(
        ambiguous_destination_mask,
        "ambiguous_destination_name",
        "medium",
    )

    # Keep generated names visible for later official-source enrichment
    generated_name_mask = app_ready_mask & review_base["name_source"].eq(
        "generated_fallback"
    )
    add_review_reason(
        generated_name_mask,
        "generated_display_name",
        "low",
    )

    review_base["review_reasons"] = [
        "; ".join(reasons_by_index[index]) for index in review_base.index
    ]

    priority_labels = {
        1: "low",
        2: "medium",
        3: "high",
    }
    review_base["review_priority"] = [
        priority_labels.get(priority_by_index[index], pd.NA)
        for index in review_base.index
    ]

    # Keep only records that triggered at least one review rule
    review_candidates = review_base[
        review_base["review_reasons"].ne("")
    ].copy()

    candidate_columns = [
        "place_id",
        "output_table",
        "review_priority",
        "review_reasons",
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
    review_candidates = review_candidates[candidate_columns]

    # Add fields for recording final manual decisions and evidence
    for column in MANUAL_REVIEW_COLUMNS:
        review_candidates[column] = pd.NA

    # Preserve completed human decisions when the candidates are regenerated
    if REVIEW_CANDIDATES_PATH.exists():
        existing_candidates = pd.read_csv(
            REVIEW_CANDIDATES_PATH,
            encoding="utf-8-sig",
        )
        preserved_columns = [
            column
            for column in MANUAL_REVIEW_COLUMNS
            if column in existing_candidates.columns
        ]

        if existing_candidates["place_id"].duplicated().any():
            raise ValueError("The existing review-candidate file has duplicate IDs.")

        if preserved_columns:
            existing_review = existing_candidates.set_index("place_id")[
                preserved_columns
            ]

            for column in preserved_columns:
                review_candidates[column] = review_candidates["place_id"].map(
                    existing_review[column]
                )

    priority_order = pd.CategoricalDtype(
        categories=["high", "medium", "low"],
        ordered=True,
    )
    review_candidates["review_priority"] = review_candidates[
        "review_priority"
    ].astype(priority_order)
    review_candidates = review_candidates.sort_values(
        [
            "review_priority",
            "output_table",
            "lga_name",
            "activity_category",
            "display_name",
        ],
        kind="stable",
    )
    review_candidates["review_priority"] = review_candidates[
        "review_priority"
    ].astype("string")

    VALIDATION_VICMAP_DIR.mkdir(parents=True, exist_ok=True)
    review_candidates.to_csv(
        REVIEW_CANDIDATES_PATH,
        index=False,
        encoding="utf-8-sig",
    )

    priority_summary = review_candidates["review_priority"].value_counts(
        sort=False
    )
    reason_summary = (
        review_candidates["review_reasons"]
        .str.split("; ")
        .explode()
        .value_counts()
    )

    print(f"\nReview candidates exported: {REVIEW_CANDIDATES_PATH}")
    print(f"Review candidate records: {len(review_candidates):,}")
    print("\nReview candidates by priority:")
    print(priority_summary.to_string())
    print("\nReview candidates by reason:")
    print(reason_summary.to_string())


def export_qa_sample(app_ready):
    """Export a reproducible sample from each council-category group."""

    # Sample small groups without requesting more rows than they contain
    samples = []

    for _, group in app_ready.groupby(
        ["lga_name", "activity_category"],
        sort=True,
    ):
        sample_size = min(SAMPLE_PER_COUNCIL_CATEGORY, len(group))
        samples.append(
            group.sample(
                n=sample_size,
                random_state=RANDOM_STATE,
            )
        )

    qa_sample = pd.concat(samples, ignore_index=True).sort_values(
        ["lga_name", "activity_category", "display_name"],
        kind="stable",
    )

    # Add fields for recording pass, issue or needs_review outcomes
    for column in QA_REVIEW_COLUMNS:
        qa_sample[column] = pd.NA

    # Preserve completed review fields when the sample is regenerated
    if QA_SAMPLE_PATH.exists():
        existing_sample = pd.read_csv(QA_SAMPLE_PATH, encoding="utf-8-sig")
        preserved_columns = [
            column for column in QA_REVIEW_COLUMNS if column in existing_sample.columns
        ]

        if preserved_columns and not existing_sample["place_id"].duplicated().any():
            existing_review = existing_sample.set_index("place_id")[preserved_columns]

            for column in preserved_columns:
                qa_sample[column] = qa_sample["place_id"].map(existing_review[column])

    VALIDATION_VICMAP_DIR.mkdir(parents=True, exist_ok=True)
    qa_sample.to_csv(QA_SAMPLE_PATH, index=False, encoding="utf-8-sig")

    print(f"\nQA sample exported: {QA_SAMPLE_PATH}")
    print(f"QA sample records: {len(qa_sample):,}")


# 8. Validation entry point
def main():
    """Run all product-level Vicmap validation checks."""

    app_ready, fallback, lga_boundaries, product_review = load_inputs()

    validate_table_structure(app_ready, "App-ready output")
    validate_table_structure(fallback, "Fallback output")
    validate_product_rules(app_ready, fallback)
    validate_product_review_application(app_ready, fallback, product_review)
    validate_spatial_assignment(app_ready, fallback, lga_boundaries)

    print_quality_summary(app_ready, fallback)
    export_review_candidates(app_ready, fallback, product_review)
    export_qa_sample(app_ready)

    print("\nVicmap product validation completed successfully.")


if __name__ == "__main__":
    main()
