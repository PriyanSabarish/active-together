"""Validate the staged Melton City Council name-enriched dataset."""

from pathlib import Path

import geopandas as gpd
import pandas as pd

# Fixed inputs and expected output
PROJECT_ROOT = Path(__file__).resolve().parents[2]
PLACES_PATH = PROJECT_ROOT / "data" / "processed" / "vicmap" / "vicmap_app_ready.csv"
RAW_DIR = PROJECT_ROOT / "data" / "raw" / "melton"
OPEN_SPACE_PATH = RAW_DIR / "melton_open_space_2026-09-10.geojson"
OVALS_PATH = RAW_DIR / "melton_ovals_and_fields_2026-09-10.geojson"
ENRICHED_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "name_enrichment"
    / "vicmap_app_ready_melton_enriched.csv"
)

EXPECTED_TOTAL = 3237
EXPECTED_TARGETS = 111
EXPECTED_UPDATED = 18
EXPECTED_RETAINED = 93

# Independent expected output and source checks.
EXPECTED_MATCHES = {
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
    """Apply the same basic name cleaning as wrangling."""

    return series.astype("string").str.strip().str.replace(r"\s+", " ", regex=True)


def prepare_source(path):
    """Load a fixed source and correct its CRS metadata."""

    source = (
        gpd.read_file(path)
        .set_crs("EPSG:28355", allow_override=True)
        .to_crs("EPSG:7855")
    )
    source["source_name"] = clean_text(source["Asset_Name"])
    source["source_record_id"] = source["Asset_Id"].astype("string")
    return source


def main():
    """Run structural, change-scope and fixed-source checks."""

    for path in [PLACES_PATH, ENRICHED_PATH, OPEN_SPACE_PATH, OVALS_PATH]:
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
        places["lga_name"].eq("MELTON")
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

    for place_id, (name, source_key, _, _) in EXPECTED_MATCHES.items():
        row = updated.loc[place_id]
        assert row["display_name"] == name
        assert row["place_name"] == name
        assert row["name_source"] == f"melton_{source_key}"

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

    # Independently confirm each approved source record and distance.
    sources = {
        "open_space": prepare_source(OPEN_SPACE_PATH),
        "ovals_and_fields": prepare_source(OVALS_PATH),
    }
    target_points = gpd.GeoDataFrame(
        targets,
        geometry=gpd.points_from_xy(targets["longitude"], targets["latitude"]),
        crs="EPSG:4326",
    ).to_crs("EPSG:7855").set_index("place_id")

    for place_id, (name, source_key, record_id, max_distance_m) in (
        EXPECTED_MATCHES.items()
    ):
        source_rows = sources[source_key].loc[
            sources[source_key]["source_record_id"].eq(record_id)
            & sources[source_key]["source_name"].eq(name)
        ]
        assert len(source_rows) == 1

        distance_m = float(
            source_rows.iloc[0].geometry.distance(
                target_points.loc[place_id].geometry
            )
        )
        assert distance_m <= max_distance_m + 0.001

    print("Melton enriched dataset validation passed.")
    print(f"Target locations: {len(targets):,}")
    print(f"Names updated: {len(changed_ids):,}")
    print(f"Generated names retained: {len(retained_ids):,}")
    print(f"Total output records: {len(enriched):,}")


if __name__ == "__main__":
    main()
