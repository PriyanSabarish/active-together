"""Apply approved Melton City Council names to a staged Vicmap dataset."""

from pathlib import Path

import geopandas as gpd
import pandas as pd

# Fixed Iteration 2 inputs and staged output
PROJECT_ROOT = Path(__file__).resolve().parents[2]
PLACES_PATH = PROJECT_ROOT / "data" / "processed" / "vicmap" / "vicmap_app_ready.csv"
RAW_DIR = PROJECT_ROOT / "data" / "raw" / "melton"
OPEN_SPACE_PATH = RAW_DIR / "melton_open_space_2026-09-10.geojson"
OVALS_PATH = RAW_DIR / "melton_ovals_and_fields_2026-09-10.geojson"
ENRICHED_OUTPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "name_enrichment"
    / "vicmap_app_ready_melton_enriched.csv"
)

EXPECTED_TARGETS = 111

# Explicit matches approved during exploration and manual map review.
APPROVED_MATCHES = {
    "vicmap_foi_1010719": ("Hillside Recreation Reserve", "open_space", "989", 55.0),
    "vicmap_foi_1252007": ("Kirkton Park", "open_space", "5684", 55.0),
    "vicmap_foi_1252039": (
        "Springside Recreation Reserve",
        "open_space",
        "2122148",
        55.0,
    ),
    "vicmap_foi_1252066": (
        "Arthur Westlake Recreation Reserve",
        "open_space",
        "351",
        55.0,
    ),
    "vicmap_foi_1252092": (
        "Arnolds Creek Linear Reserve West Branch - Westlakes",
        "open_space",
        "1769",
        55.0,
    ),
    "vicmap_foi_1252094": (
        "Blackwood Drive Recreation Reserve",
        "open_space",
        "422",
        55.0,
    ),
    "vicmap_foi_1252098": ("Lachlan Lane Closure", "open_space", "1143", 55.0),
    "vicmap_foi_1252279": (
        "Diggers Rest Recreation Reserve",
        "open_space",
        "719",
        55.0,
    ),
    "vicmap_foi_1275017": (
        "St Arnaud Rd Streetscape (South)",
        "open_space",
        "48814",
        55.0,
    ),
    "vicmap_foi_1313706": (
        "Botanica Springs Linear Reserve",
        "open_space",
        "46141",
        55.0,
    ),
    "vicmap_foi_1335077": ("Lawler Rd Linear Reserve", "open_space", "2175432", 55.0),
    "vicmap_foi_1340990": ("Horsley St Reserve", "open_space", "2173130", 55.0),
    "vicmap_foi_1341389": ("Lake Caroline Waterfront", "open_space", "2018638", 55.0),
    "vicmap_foi_638764": (
        "Arnolds Creek South of Brooklyn Road Environmental Reserve",
        "open_space",
        "49458",
        55.0,
    ),
    "vicmap_foi_638797": ("Taylors Hill Central Park", "open_space", "1652", 55.0),
    "vicmap_foi_75689": ("MacPherson Park", "open_space", "1212", 55.0),
    "vicmap_foi_76020": (
        "Blackwood Drive Recreation Reserve",
        "open_space",
        "422",
        55.0,
    ),
    "vicmap_foi_75891": (
        "Kurunjang Recreation Reserve - Cricket/Football Oval",
        "ovals_and_fields",
        "5198",
        80.0,
    ),
}


def clean_text(series):
    """Trim whitespace and remove unusable names."""

    cleaned = series.astype("string").str.strip().str.replace(r"\s+", " ", regex=True)
    invalid = {"", "NO DATA", "N/A", "NA", "UNKNOWN", "UNNAMED"}
    return cleaned.mask(cleaned.str.upper().isin(invalid))


def load_inputs():
    """Load the baseline and both fixed official snapshots."""

    for path in [PLACES_PATH, OPEN_SPACE_PATH, OVALS_PATH]:
        if not path.exists():
            raise FileNotFoundError(f"Required input not found: {path}")

    places = pd.read_csv(PLACES_PATH, encoding="utf-8-sig")
    open_space = gpd.read_file(OPEN_SPACE_PATH)
    ovals = gpd.read_file(OVALS_PATH)

    print("Places loaded:", len(places))
    print("Open-space records loaded:", len(open_space))
    print("Oval records loaded:", len(ovals))

    return places, open_space, ovals


def check_inputs(places, open_space, ovals):
    """Check fields required by the reviewed rules."""

    place_columns = {
        "place_id",
        "display_name",
        "place_name",
        "name_source",
        "activity_category",
        "feature_subtype",
        "lga_name",
        "longitude",
        "latitude",
    }
    source_columns = {
        "Asset_Id",
        "Asset_Name",
        "Asset_Type",
        "Asset_Subt",
        "Locality",
        "geometry",
    }

    checks = [
        ("places", place_columns - set(places.columns)),
        ("open space", source_columns - set(open_space.columns)),
        ("ovals", source_columns - set(ovals.columns)),
    ]
    for label, missing in checks:
        if missing:
            raise ValueError(f"Missing {label} columns: {sorted(missing)}")


def prepare_targets(places):
    """Select Melton records that still use generated names."""

    targets = places.loc[
        places["lga_name"].astype("string").str.strip().str.upper().eq("MELTON")
        & places["name_source"].astype("string").str.strip().eq(
            "generated_from_subtype"
        )
    ].copy()

    targets["longitude"] = pd.to_numeric(targets["longitude"], errors="coerce")
    targets["latitude"] = pd.to_numeric(targets["latitude"], errors="coerce")

    if len(targets) != EXPECTED_TARGETS:
        raise ValueError(
            f"Expected {EXPECTED_TARGETS} Melton targets, got {len(targets)}."
        )
    if targets["place_id"].duplicated().any():
        raise ValueError("Melton targets contain duplicate place IDs.")
    if targets[["longitude", "latitude"]].isna().any().any():
        raise ValueError("Melton targets contain missing coordinates.")

    return gpd.GeoDataFrame(
        targets,
        geometry=gpd.points_from_xy(targets["longitude"], targets["latitude"]),
        crs="EPSG:4326",
    )


def prepare_source(frame):
    """Correct the source CRS metadata and standardise source fields."""

    prepared = (
        frame.set_crs("EPSG:28355", allow_override=True)
        .to_crs("EPSG:7855")
        .copy()
    )
    prepared["source_name"] = clean_text(prepared["Asset_Name"])
    prepared["source_record_id"] = prepared["Asset_Id"].astype("string")
    return prepared


def create_candidates(targets, sources):
    """Recreate only the 18 manually approved Melton matches."""

    target_ids = set(targets["place_id"])
    missing_ids = set(APPROVED_MATCHES) - target_ids
    if missing_ids:
        raise ValueError(f"Approved target IDs are missing: {sorted(missing_ids)}")

    targets_m = targets.to_crs("EPSG:7855").set_index("place_id")
    snapshot_names = {
        "open_space": OPEN_SPACE_PATH.name,
        "ovals_and_fields": OVALS_PATH.name,
    }
    rows = []

    for place_id, (name, source_key, record_id, max_distance_m) in (
        APPROVED_MATCHES.items()
    ):
        target = targets_m.loc[place_id]
        source = sources[source_key]
        matched_source = source.loc[
            source["source_record_id"].eq(record_id)
            & source["source_name"].eq(name)
        ]

        if len(matched_source) != 1:
            raise ValueError(
                f"Expected one source record for {place_id}, got {len(matched_source)}."
            )

        source_row = matched_source.iloc[0]
        distance_m = float(source_row.geometry.distance(target.geometry))
        if distance_m > max_distance_m + 0.001:
            raise ValueError(
                f"Reviewed distance changed for {place_id}: {distance_m:.3f} m"
            )

        rows.append(
            {
                "place_id": place_id,
                "original_display_name": target["display_name"],
                "proposed_name": name,
                "proposed_name_source": f"melton_{source_key}",
                "match_method": "manually_reviewed_nearest_official_feature",
                "match_distance_m": round(distance_m, 3),
                "activity_category": target["activity_category"],
                "feature_subtype": target["feature_subtype"],
                "longitude": target["longitude"],
                "latitude": target["latitude"],
                "source_record_id": record_id,
                "source_snapshot": snapshot_names[source_key],
            }
        )

    candidates = pd.DataFrame(rows).sort_values("place_id").reset_index(drop=True)
    if len(candidates) != len(APPROVED_MATCHES):
        raise ValueError("Not every approved Melton match was recreated.")

    print("Approved Melton names recreated:", len(candidates))
    return candidates


def create_enriched_output(places, candidates):
    """Apply approved names to a copy of the complete baseline."""

    original_columns = list(places.columns)
    updates = candidates[
        ["place_id", "proposed_name", "proposed_name_source"]
    ].copy()

    enriched = places.merge(updates, on="place_id", how="left", validate="one_to_one")
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
        raise ValueError("Not every approved name was applied exactly once.")

    return enriched[original_columns].copy()


def save_output(enriched):
    """Save one staged Melton-enriched CSV."""

    ENRICHED_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    enriched.to_csv(ENRICHED_OUTPUT_PATH, index=False, encoding="utf-8-sig")
    print("Enriched file saved:", ENRICHED_OUTPUT_PATH)


def main():
    """Run the Melton name-wrangling stage."""

    places, open_space, ovals = load_inputs()
    check_inputs(places, open_space, ovals)
    targets = prepare_targets(places)
    sources = {
        "open_space": prepare_source(open_space),
        "ovals_and_fields": prepare_source(ovals),
    }
    candidates = create_candidates(targets, sources)
    enriched = create_enriched_output(places, candidates)
    save_output(enriched)

    print("Melton generated-name targets:", len(targets))
    print("Names updated:", len(candidates))
    print("Generated names retained:", len(targets) - len(candidates))
    print("Total output records:", len(enriched))
    print("Melton name wrangling completed successfully.")


if __name__ == "__main__":
    main()
