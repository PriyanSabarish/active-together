"""Validate the staged City of Melbourne name-enriched dataset."""

from pathlib import Path

import geopandas as gpd
import pandas as pd

# Fixed inputs and staged output
PROJECT_ROOT = Path(__file__).resolve().parents[2]
PLACES_PATH = PROJECT_ROOT / "data" / "processed" / "vicmap" / "vicmap_app_ready.csv"
RAW_DIR = PROJECT_ROOT / "data" / "raw" / "melbourne"
PLAYGROUNDS_PATH = (
    RAW_DIR / "city_of_melbourne_playgrounds_2026-09-10.geojson"
)
LANDMARKS_PATH = (
    RAW_DIR / "city_of_melbourne_landmarks_2026-09-10.geojson"
)
ENRICHED_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "name_enrichment"
    / "vicmap_app_ready_melbourne_enriched.csv"
)

EXPECTED_TOTAL = 3237
EXPECTED_TARGETS = 27
EXPECTED_UPDATED = 8
EXPECTED_RETAINED = 19

# Expected outputs and their reviewed spatial limits.
EXPECTED_MATCHES = {
    "vicmap_foi_1183091": (
        "Eades Park Playground",
        "playgrounds",
        0.0,
        True,
    ),
    "vicmap_foi_1183092": (
        "Eades Park Playground",
        "playgrounds",
        0.0,
        True,
    ),
    "vicmap_foi_985961": (
        "Holland Park Playground",
        "playgrounds",
        0.0,
        True,
    ),
    "vicmap_foi_1002117": (
        "Gardiner Reserve Playground",
        "playgrounds",
        1.0,
        False,
    ),
    "vicmap_foi_1206821": (
        "State Netball Hockey Centre",
        "landmarks",
        150.0,
        False,
    ),
    "vicmap_foi_1206848": (
        "State Netball Hockey Centre",
        "landmarks",
        150.0,
        False,
    ),
    "vicmap_foi_1206820": (
        "State Netball Hockey Centre",
        "landmarks",
        150.0,
        False,
    ),
    "vicmap_foi_1002109": (
        "Docklands Park",
        "landmarks",
        150.0,
        False,
    ),
}


def clean_text(series):
    """Apply the same basic name cleaning as wrangling."""

    return series.astype("string").str.strip().str.replace(r"\s+", " ", regex=True)


def main():
    """Run structural, change-scope and source checks."""

    for path in [PLACES_PATH, ENRICHED_PATH, PLAYGROUNDS_PATH, LANDMARKS_PATH]:
        if not path.exists():
            raise FileNotFoundError(f"Required input not found: {path}")

    places = pd.read_csv(PLACES_PATH, encoding="utf-8-sig")
    enriched = pd.read_csv(ENRICHED_PATH, encoding="utf-8-sig")

    # Confirm that the complete dataset structure is unchanged.
    assert len(places) == len(enriched) == EXPECTED_TOTAL
    assert places["place_id"].is_unique
    assert enriched["place_id"].is_unique
    assert list(places.columns) == list(enriched.columns)
    assert set(places["place_id"]) == set(enriched["place_id"])

    targets = places.loc[
        places["lga_name"].eq("MELBOURNE")
        & places["name_source"].eq("generated_from_subtype")
    ].copy()
    assert len(targets) == EXPECTED_TARGETS

    original = places.set_index("place_id").sort_index()
    updated = enriched.set_index("place_id").sort_index()

    name_columns = ["display_name", "place_name", "name_source"]
    stable_columns = [
        column for column in places.columns if column not in {"place_id", *name_columns}
    ]

    # Only name-related fields may change.
    assert original[stable_columns].equals(updated[stable_columns])

    changed_mask = original[name_columns].ne(updated[name_columns]).any(axis=1)
    changed_ids = set(original.index[changed_mask])
    assert changed_ids == set(EXPECTED_MATCHES)
    assert len(changed_ids) == EXPECTED_UPDATED

    for place_id, (name, source, _, _) in EXPECTED_MATCHES.items():
        row = updated.loc[place_id]
        assert row["display_name"] == name
        assert row["place_name"] == name
        assert row["name_source"] == f"city_of_melbourne_{source}"

    changed = updated.loc[sorted(changed_ids)]
    assert changed["display_name"].notna().all()
    assert changed["display_name"].eq(changed["display_name"].str.strip()).all()
    assert not changed["display_name"].str.contains(r"\s{2,}", regex=True).any()
    assert not changed["display_name"].str.lower().str.startswith("unnamed").any()

    retained_ids = set(targets["place_id"]) - changed_ids
    assert len(retained_ids) == EXPECTED_RETAINED
    assert updated.loc[sorted(retained_ids), "name_source"].eq(
        "generated_from_subtype"
    ).all()

    # Independently confirm every accepted name and spatial limit.
    playgrounds = gpd.read_file(PLAYGROUNDS_PATH).to_crs("EPSG:7855")
    landmarks = gpd.read_file(LANDMARKS_PATH).to_crs("EPSG:7855")
    playgrounds["source_name"] = clean_text(playgrounds["name"])
    landmarks["source_name"] = clean_text(landmarks["feature_name"])

    target_points = gpd.GeoDataFrame(
        targets,
        geometry=gpd.points_from_xy(targets["longitude"], targets["latitude"]),
        crs="EPSG:4326",
    ).to_crs("EPSG:7855").set_index("place_id")

    sources = {"playgrounds": playgrounds, "landmarks": landmarks}
    for place_id, (name, source_key, max_distance, require_within) in (
        EXPECTED_MATCHES.items()
    ):
        target_geometry = target_points.loc[place_id].geometry
        source_rows = sources[source_key].loc[
            sources[source_key]["source_name"].eq(name)
        ]
        assert not source_rows.empty

        distances = source_rows.geometry.distance(target_geometry)
        nearest_geometry = source_rows.loc[distances.idxmin()].geometry
        assert float(distances.min()) <= max_distance + 0.001

        if require_within:
            assert target_geometry.within(nearest_geometry)

    print("Melbourne enriched dataset validation passed.")
    print(f"Target locations: {len(targets):,}")
    print(f"Names updated: {len(changed_ids):,}")
    print(f"Generated names retained: {len(retained_ids):,}")
    print(f"Total output records: {len(enriched):,}")


if __name__ == "__main__":
    main()
