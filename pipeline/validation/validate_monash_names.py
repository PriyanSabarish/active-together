"""Validate the staged Monash name-enriched dataset."""

from pathlib import Path

import geopandas as gpd
import pandas as pd

# Project paths
PROJECT_ROOT = Path(__file__).resolve().parents[2]

PLACES_PATH = PROJECT_ROOT / "data" / "processed" / "vicmap" / "vicmap_app_ready.csv"

ENRICHED_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "name_enrichment"
    / "vicmap_app_ready_monash_enriched.csv"
)

VPA_SNAPSHOT_PATH = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "monash"
    / "vpa_open_space_monash_2026-09-10.geojson"
)

EXPECTED_TARGETS = 565
EXPECTED_CANDIDATES = 491
EXPECTED_UNMATCHED = 74


def clean_text(series):
    """Apply the same name cleaning used during wrangling."""

    return series.astype("string").str.strip().str.replace(r"\s+", " ", regex=True)


def main():
    """Run full-output and spatial validation checks."""

    places = pd.read_csv(
        PLACES_PATH,
        encoding="utf-8-sig",
    )

    enriched = pd.read_csv(
        ENRICHED_PATH,
        encoding="utf-8-sig",
    )

    assert len(places) == len(enriched) == 3237
    assert places["place_id"].is_unique
    assert enriched["place_id"].is_unique
    assert list(places.columns) == list(enriched.columns)
    assert set(places["place_id"]) == set(enriched["place_id"])

    # Recreate the intended Monash target population.
    targets = places.loc[
        places["lga_name"].eq("MONASH")
        & places["name_source"].eq("generated_from_subtype")
    ].copy()

    assert len(targets) == EXPECTED_TARGETS

    original = places.set_index("place_id").sort_index()
    updated = enriched.set_index("place_id").sort_index()

    name_columns = ["display_name", "place_name", "name_source"]
    stable_columns = [
        column for column in places.columns if column not in {"place_id", *name_columns}
    ]

    # All non-name fields must remain unchanged.
    assert original[stable_columns].equals(updated[stable_columns])

    changed_mask = original[name_columns].ne(updated[name_columns]).any(axis=1)
    changed_ids = set(original.index[changed_mask])

    assert len(changed_ids) == EXPECTED_CANDIDATES
    assert changed_ids.issubset(set(targets["place_id"]))

    changed = updated.loc[sorted(changed_ids)].copy()
    assert changed["display_name"].eq(changed["place_name"]).all()
    assert changed["name_source"].eq("vpa_open_space").all()
    assert changed["display_name"].notna().all()
    assert changed["display_name"].eq(changed["display_name"].str.strip()).all()
    assert not changed["display_name"].str.contains(r"\s{2,}", regex=True).any()
    assert not changed["display_name"].str.lower().str.startswith("unnamed").any()

    retained_ids = set(targets["place_id"]) - changed_ids
    assert len(retained_ids) == EXPECTED_UNMATCHED
    assert updated.loc[sorted(retained_ids), "name_source"].eq(
        "generated_from_subtype"
    ).all()

    # Independently recreate the VPA spatial matches.
    if not VPA_SNAPSHOT_PATH.exists():
        raise FileNotFoundError(f"VPA snapshot not found: {VPA_SNAPSHOT_PATH}")

    vpa = gpd.read_file(VPA_SNAPSHOT_PATH).to_crs("EPSG:4326")
    vpa["LGA"] = clean_text(vpa["LGA"]).str.upper()
    vpa["vpa_name_clean"] = clean_text(vpa["PARK_NAME"])

    invalid_names = {"", "NO DATA", "N/A", "NA", "UNKNOWN", "UNNAMED"}
    vpa.loc[
        vpa["vpa_name_clean"].str.upper().isin(invalid_names), "vpa_name_clean"
    ] = pd.NA

    named_polygons = vpa.loc[
        vpa["LGA"].eq("MONASH") & vpa["vpa_name_clean"].notna(),
        ["FID", "vpa_name_clean", "geometry"],
    ].copy()

    target_points = gpd.GeoDataFrame(
        targets,
        geometry=gpd.points_from_xy(targets["longitude"], targets["latitude"]),
        crs="EPSG:4326",
    )

    expected_matches = gpd.sjoin(
        target_points,
        named_polygons,
        how="inner",
        predicate="within",
    )

    assert not expected_matches["place_id"].duplicated().any()
    assert len(expected_matches) == EXPECTED_CANDIDATES
    assert set(expected_matches["place_id"]) == changed_ids

    expected_names = expected_matches[["place_id", "vpa_name_clean"]]
    actual_names = enriched[["place_id", "display_name"]]

    name_check = expected_names.merge(
        actual_names,
        on="place_id",
        how="inner",
        validate="one_to_one",
    )
    assert name_check["display_name"].eq(name_check["vpa_name_clean"]).all()

    print("Monash enriched dataset validation passed.")
    print(f"Target locations: {len(targets):,}")
    print(f"Names updated: {len(changed_ids):,}")
    print(f"Generated names retained: {len(retained_ids):,}")
    print(f"Total output records: {len(enriched):,}")


if __name__ == "__main__":
    main()
