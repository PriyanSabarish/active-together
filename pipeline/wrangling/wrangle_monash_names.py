"""Create VPA name candidates for generated Monash locations."""

from pathlib import Path

import geopandas as gpd
import pandas as pd

# Project paths
PROJECT_ROOT = Path(__file__).resolve().parents[2]

PLACES_PATH = PROJECT_ROOT / "data" / "processed" / "vicmap" / "vicmap_app_ready.csv"

VPA_SNAPSHOT_PATH = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "monash"
    / "vpa_open_space_monash_2026-09-10.geojson"
)

ENRICHED_OUTPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "name_enrichment"
    / "vicmap_app_ready_monash_enriched.csv"
)


def clean_text(series):
    """Trim whitespace and remove invalid names."""

    cleaned = series.astype("string").str.strip().str.replace(r"\s+", " ", regex=True)

    invalid_values = {
        "",
        "NO DATA",
        "N/A",
        "NA",
        "UNKNOWN",
        "UNNAMED",
    }

    return cleaned.mask(cleaned.str.upper().isin(invalid_values))


def load_inputs():
    """Load Iteration 1 places and the fixed VPA snapshot."""

    if not PLACES_PATH.exists():
        raise FileNotFoundError(f"Places file not found: {PLACES_PATH}")
    if not VPA_SNAPSHOT_PATH.exists():
        raise FileNotFoundError(f"VPA snapshot not found: {VPA_SNAPSHOT_PATH}")

    places = pd.read_csv(
        PLACES_PATH,
        encoding="utf-8-sig",
    )

    vpa = gpd.read_file(VPA_SNAPSHOT_PATH)

    print("Places loaded:", len(places))
    print("VPA polygons loaded:", len(vpa))
    print("VPA snapshot:", VPA_SNAPSHOT_PATH.name)

    return places, vpa, VPA_SNAPSHOT_PATH


def check_input_columns(places, vpa):
    """Check fields required by the wrangling rules."""

    required_place_columns = {
        "place_id",
        "display_name",
        "name_source",
        "activity_category",
        "feature_subtype",
        "lga_name",
        "longitude",
        "latitude",
    }

    required_vpa_columns = {
        "FID",
        "PARK_NAME",
        "LGA",
        "OS_CATEGOR",
        "OS_CATEG_2",
        "OS_STATUS",
        "OS_ACCESS",
        "geometry",
    }

    missing_places = required_place_columns - set(places.columns)

    missing_vpa = required_vpa_columns - set(vpa.columns)

    if missing_places:
        raise ValueError(f"Missing place columns: {sorted(missing_places)}")

    if missing_vpa:
        raise ValueError(f"Missing VPA columns: {sorted(missing_vpa)}")

    if vpa.crs is None:
        raise ValueError("The VPA snapshot has no coordinate system.")


def prepare_targets(places):
    """Select Monash records with generated names."""

    monash_mask = (
        places["lga_name"].astype("string").str.strip().str.upper().eq("MONASH")
    )

    generated_mask = (
        places["name_source"].astype("string").str.strip().eq("generated_from_subtype")
    )

    targets = places.loc[monash_mask & generated_mask].copy()

    targets["longitude"] = pd.to_numeric(
        targets["longitude"],
        errors="coerce",
    )

    targets["latitude"] = pd.to_numeric(
        targets["latitude"],
        errors="coerce",
    )

    if targets["place_id"].duplicated().any():
        raise ValueError("Monash targets contain duplicate place IDs.")

    if targets[["longitude", "latitude"]].isna().any().any():
        raise ValueError("Monash targets contain missing coordinates.")

    print("Monash generated-name targets:", len(targets))

    return gpd.GeoDataFrame(
        targets,
        geometry=gpd.points_from_xy(
            targets["longitude"],
            targets["latitude"],
        ),
        crs="EPSG:4326",
    )


def prepare_vpa_polygons(vpa):
    """Clean VPA names and keep named Monash polygons."""

    vpa = vpa.copy()
    vpa["LGA"] = clean_text(vpa["LGA"]).str.upper()
    vpa["park_name_clean"] = clean_text(vpa["PARK_NAME"])

    named_polygons = vpa.loc[
        vpa["LGA"].eq("MONASH") & vpa["park_name_clean"].notna(),
        [
            "FID",
            "PARK_NAME",
            "park_name_clean",
            "OS_CATEGOR",
            "OS_CATEG_2",
            "OS_STATUS",
            "OS_ACCESS",
            "geometry",
        ],
    ].copy()

    named_polygons = named_polygons.to_crs("EPSG:4326")

    if named_polygons["FID"].duplicated().any():
        raise ValueError("Named VPA polygons contain duplicate FIDs.")

    print("Named Monash VPA polygons:", len(named_polygons))

    return named_polygons


def create_candidates(targets, polygons, snapshot_name):
    """Match each target to its containing named polygon."""

    matches = gpd.sjoin(
        targets,
        polygons,
        how="left",
        predicate="within",
    )

    matched = matches.loc[matches["park_name_clean"].notna()].copy()

    duplicate_match = matched["place_id"].duplicated(keep=False)

    if duplicate_match.any():
        duplicate_count = matched.loc[
            duplicate_match,
            "place_id",
        ].nunique()

        raise ValueError(
            f"{duplicate_count} targets matched multiple " "named VPA polygons."
        )

    candidates = matched.rename(
        columns={
            "display_name": "original_display_name",
            "park_name_clean": "proposed_name",
            "FID": "vpa_fid",
            "PARK_NAME": "vpa_name_raw",
            "OS_CATEGOR": "vpa_category",
            "OS_CATEG_2": "vpa_category_secondary",
            "OS_STATUS": "vpa_status",
            "OS_ACCESS": "vpa_access",
        }
    )

    candidates["proposed_name_source"] = "vpa_open_space"

    candidates["match_method"] = "point_within_named_polygon"

    candidates["match_scope"] = "containing_open_space"

    candidates["vpa_snapshot"] = snapshot_name

    output_columns = [
        "place_id",
        "original_display_name",
        "proposed_name",
        "proposed_name_source",
        "match_method",
        "match_scope",
        "activity_category",
        "feature_subtype",
        "longitude",
        "latitude",
        "vpa_fid",
        "vpa_name_raw",
        "vpa_category",
        "vpa_category_secondary",
        "vpa_status",
        "vpa_access",
        "vpa_snapshot",
    ]

    candidates = (
        candidates[output_columns].sort_values("place_id").reset_index(drop=True)
    )

    print("VPA name candidates created:", len(candidates))

    return candidates


def create_enriched_output(places, candidates):
    """Apply VPA names to a copy of the complete dataset."""

    original_columns = list(places.columns)
    name_updates = candidates[
        ["place_id", "proposed_name", "proposed_name_source"]
    ].copy()

    enriched = places.merge(
        name_updates,
        on="place_id",
        how="left",
        validate="one_to_one",
    )

    update_mask = enriched["proposed_name"].notna()

    # Change only the three name-related fields.
    enriched.loc[update_mask, "display_name"] = enriched.loc[
        update_mask, "proposed_name"
    ]
    enriched.loc[update_mask, "place_name"] = enriched.loc[
        update_mask, "proposed_name"
    ]
    enriched.loc[update_mask, "name_source"] = enriched.loc[
        update_mask, "proposed_name_source"
    ]

    if int(update_mask.sum()) != len(candidates):
        raise ValueError("Not every candidate was applied exactly once.")

    enriched = enriched[original_columns].copy()

    print("Names updated:", int(update_mask.sum()))
    print("Total output records:", len(enriched))

    return enriched


def save_enriched_output(enriched):
    """Save the staged Iteration 2 dataset."""

    ENRICHED_OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    enriched.to_csv(
        ENRICHED_OUTPUT_PATH,
        index=False,
        encoding="utf-8-sig",
    )

    print("Enriched file saved:", ENRICHED_OUTPUT_PATH)


def main():
    """Run the Monash name-wrangling process."""

    places, vpa, vpa_path = load_inputs()

    check_input_columns(places, vpa)

    targets = prepare_targets(places)
    polygons = prepare_vpa_polygons(vpa)

    candidates = create_candidates(
        targets,
        polygons,
        snapshot_name=vpa_path.name,
    )

    enriched = create_enriched_output(places, candidates)
    save_enriched_output(enriched)

    print("Monash name wrangling completed successfully.")


if __name__ == "__main__":
    main()
