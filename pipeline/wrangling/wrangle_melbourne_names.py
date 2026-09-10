"""Apply approved City of Melbourne names to a staged Vicmap dataset."""

from pathlib import Path

import geopandas as gpd
import pandas as pd

# Fixed Iteration 2 inputs and staged output
PROJECT_ROOT = Path(__file__).resolve().parents[2]
PLACES_PATH = PROJECT_ROOT / "data" / "processed" / "vicmap" / "vicmap_app_ready.csv"
RAW_DIR = PROJECT_ROOT / "data" / "raw" / "melbourne"
PLAYGROUNDS_PATH = (
    RAW_DIR / "city_of_melbourne_playgrounds_2026-09-10.geojson"
)
LANDMARKS_PATH = (
    RAW_DIR / "city_of_melbourne_landmarks_2026-09-10.geojson"
)
ENRICHED_OUTPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "name_enrichment"
    / "vicmap_app_ready_melbourne_enriched.csv"
)

EXPECTED_TARGETS = 27

# These eight matches were accepted during the exploration and manual review.
APPROVED_MATCHES = {
    "vicmap_foi_1183091": {
        "name": "Eades Park Playground",
        "source": "playgrounds",
        "method": "point_within_named_polygon",
        "scope": "containing_playground",
        "max_distance_m": 0.0,
    },
    "vicmap_foi_1183092": {
        "name": "Eades Park Playground",
        "source": "playgrounds",
        "method": "point_within_named_polygon",
        "scope": "containing_playground",
        "max_distance_m": 0.0,
    },
    "vicmap_foi_985961": {
        "name": "Holland Park Playground",
        "source": "playgrounds",
        "method": "point_within_named_polygon",
        "scope": "containing_playground",
        "max_distance_m": 0.0,
    },
    "vicmap_foi_1002117": {
        "name": "Gardiner Reserve Playground",
        "source": "playgrounds",
        "method": "reviewed_nearest_playground",
        "scope": "nearby_playground",
        "max_distance_m": 1.0,
    },
    "vicmap_foi_1206821": {
        "name": "State Netball Hockey Centre",
        "source": "landmarks",
        "method": "reviewed_nearest_landmark",
        "scope": "containing_facility_complex",
        "max_distance_m": 150.0,
    },
    "vicmap_foi_1206848": {
        "name": "State Netball Hockey Centre",
        "source": "landmarks",
        "method": "reviewed_nearest_landmark",
        "scope": "containing_facility_complex",
        "max_distance_m": 150.0,
    },
    "vicmap_foi_1206820": {
        "name": "State Netball Hockey Centre",
        "source": "landmarks",
        "method": "reviewed_nearest_landmark",
        "scope": "containing_facility_complex",
        "max_distance_m": 150.0,
    },
    "vicmap_foi_1002109": {
        "name": "Docklands Park",
        "source": "landmarks",
        "method": "reviewed_nearest_landmark",
        "scope": "containing_recreation_area",
        "max_distance_m": 150.0,
    },
}


def clean_text(series):
    """Trim whitespace and remove unusable names."""

    cleaned = series.astype("string").str.strip().str.replace(r"\s+", " ", regex=True)
    invalid = {"", "NO DATA", "N/A", "NA", "UNKNOWN", "UNNAMED"}
    return cleaned.mask(cleaned.str.upper().isin(invalid))


def load_inputs():
    """Load the baseline and both fixed official snapshots."""

    for path in [PLACES_PATH, PLAYGROUNDS_PATH, LANDMARKS_PATH]:
        if not path.exists():
            raise FileNotFoundError(f"Required input not found: {path}")

    places = pd.read_csv(PLACES_PATH, encoding="utf-8-sig")
    playgrounds = gpd.read_file(PLAYGROUNDS_PATH)
    landmarks = gpd.read_file(LANDMARKS_PATH)

    print("Places loaded:", len(places))
    print("Playgrounds loaded:", len(playgrounds))
    print("Landmarks loaded:", len(landmarks))

    return places, playgrounds, landmarks


def check_inputs(places, playgrounds, landmarks):
    """Check the fields required by the reviewed rules."""

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
    playground_columns = {"name", "council_re", "features", "geometry"}
    landmark_columns = {"theme", "sub_theme", "feature_name", "geometry"}

    checks = [
        ("places", place_columns - set(places.columns)),
        ("playgrounds", playground_columns - set(playgrounds.columns)),
        ("landmarks", landmark_columns - set(landmarks.columns)),
    ]
    for label, missing in checks:
        if missing:
            raise ValueError(f"Missing {label} columns: {sorted(missing)}")

    if playgrounds.crs is None or landmarks.crs is None:
        raise ValueError("A City of Melbourne snapshot has no coordinate system.")


def prepare_targets(places):
    """Select Melbourne records that still use generated names."""

    targets = places.loc[
        places["lga_name"].astype("string").str.strip().str.upper().eq("MELBOURNE")
        & places["name_source"].astype("string").str.strip().eq(
            "generated_from_subtype"
        )
    ].copy()

    targets["longitude"] = pd.to_numeric(targets["longitude"], errors="coerce")
    targets["latitude"] = pd.to_numeric(targets["latitude"], errors="coerce")

    if len(targets) != EXPECTED_TARGETS:
        raise ValueError(f"Expected {EXPECTED_TARGETS} Melbourne targets, got {len(targets)}.")
    if targets["place_id"].duplicated().any():
        raise ValueError("Melbourne targets contain duplicate place IDs.")
    if targets[["longitude", "latitude"]].isna().any().any():
        raise ValueError("Melbourne targets contain missing coordinates.")

    print("Melbourne generated-name targets:", len(targets))

    return gpd.GeoDataFrame(
        targets,
        geometry=gpd.points_from_xy(targets["longitude"], targets["latitude"]),
        crs="EPSG:4326",
    )


def prepare_sources(playgrounds, landmarks):
    """Clean official names and keep the reviewed source fields."""

    playgrounds = playgrounds.to_crs("EPSG:4326").copy()
    playgrounds["source_name"] = clean_text(playgrounds["name"])
    playgrounds["source_record_id"] = playgrounds["council_re"].astype("string")
    playgrounds["source_detail"] = playgrounds["features"].astype("string")

    landmarks = landmarks.to_crs("EPSG:4326").copy()
    landmarks["source_name"] = clean_text(landmarks["feature_name"])
    landmarks["source_record_id"] = pd.NA
    landmarks["source_detail"] = landmarks["sub_theme"].astype("string")

    return {
        "playgrounds": playgrounds,
        "landmarks": landmarks,
    }


def create_candidates(targets, sources):
    """Recreate only the eight matches approved during exploration."""

    target_ids = set(targets["place_id"])
    missing_ids = set(APPROVED_MATCHES) - target_ids
    if missing_ids:
        raise ValueError(f"Approved target IDs are missing: {sorted(missing_ids)}")

    targets_projected = targets.to_crs("EPSG:7855").set_index("place_id")
    sources_projected = {
        key: frame.to_crs("EPSG:7855") for key, frame in sources.items()
    }

    rows = []
    for place_id, rule in APPROVED_MATCHES.items():
        target = targets_projected.loc[place_id]
        source = sources_projected[rule["source"]]
        named = source.loc[source["source_name"].eq(rule["name"])].copy()

        if named.empty:
            raise ValueError(f"Approved source name not found: {rule['name']}")

        distances = named.geometry.distance(target.geometry)
        source_row = named.loc[distances.idxmin()]
        distance_m = float(distances.min())

        if distance_m > rule["max_distance_m"] + 0.001:
            raise ValueError(
                f"Reviewed distance changed for {place_id}: {distance_m:.3f} m"
            )

        if rule["method"] == "point_within_named_polygon" and not target.geometry.within(
            source_row.geometry
        ):
            raise ValueError(f"Reviewed containment no longer holds for {place_id}.")

        rows.append(
            {
                "place_id": place_id,
                "original_display_name": target["display_name"],
                "proposed_name": rule["name"],
                "proposed_name_source": (
                    f"city_of_melbourne_{rule['source']}"
                ),
                "match_method": rule["method"],
                "match_scope": rule["scope"],
                "match_distance_m": round(distance_m, 3),
                "activity_category": target["activity_category"],
                "feature_subtype": target["feature_subtype"],
                "longitude": target["longitude"],
                "latitude": target["latitude"],
                "source_record_id": source_row["source_record_id"],
                "source_detail": source_row["source_detail"],
                "source_snapshot": (
                    PLAYGROUNDS_PATH.name
                    if rule["source"] == "playgrounds"
                    else LANDMARKS_PATH.name
                ),
            }
        )

    candidates = pd.DataFrame(rows).sort_values("place_id").reset_index(drop=True)
    if len(candidates) != len(APPROVED_MATCHES):
        raise ValueError("Not every approved Melbourne match was recreated.")

    print("Approved Melbourne names recreated:", len(candidates))
    return candidates


def create_enriched_output(places, candidates):
    """Apply approved names to a copy of the complete baseline."""

    original_columns = list(places.columns)
    updates = candidates[
        ["place_id", "proposed_name", "proposed_name_source"]
    ].copy()

    enriched = places.merge(
        updates,
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
        raise ValueError("Not every approved name was applied exactly once.")

    return enriched[original_columns].copy()


def save_output(enriched):
    """Save one staged Melbourne-enriched CSV."""

    ENRICHED_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    enriched.to_csv(ENRICHED_OUTPUT_PATH, index=False, encoding="utf-8-sig")
    print("Enriched file saved:", ENRICHED_OUTPUT_PATH)


def main():
    """Run the Melbourne name-wrangling stage."""

    places, playgrounds, landmarks = load_inputs()
    check_inputs(places, playgrounds, landmarks)
    targets = prepare_targets(places)
    sources = prepare_sources(playgrounds, landmarks)
    candidates = create_candidates(targets, sources)
    enriched = create_enriched_output(places, candidates)
    save_output(enriched)

    print("Names updated:", len(candidates))
    print("Generated names retained:", len(targets) - len(candidates))
    print("Total output records:", len(enriched))
    print("Melbourne name wrangling completed successfully.")


if __name__ == "__main__":
    main()
